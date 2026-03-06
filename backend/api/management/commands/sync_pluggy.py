"""
Management command to sync transactions from Pluggy Open Finance API.

Usage:
    python manage.py sync_pluggy --profile Palmer
    python manage.py sync_pluggy --profile Palmer --from 2024-01-01 --to 2026-03-04
    python manage.py sync_pluggy --profile Palmer --accounts checking,master
    python manage.py sync_pluggy --profile Palmer --dry-run
    python manage.py sync_pluggy --profile Rafa --item 68058e60-...
"""

import os
import re
import logging
import unicodedata
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import (
    Account, BalanceAnchor, Category,
    PluggyCategoryMapping, Profile, RenameRule, Transaction,
)
from api.pluggy import PluggyClient

logger = logging.getLogger(__name__)

# Per-profile Pluggy item IDs and account mappings.
# Maps pluggy_account_id -> vault_account_name.
# Items without explicit mapping use auto-discovery (match by account type).
PROFILE_CONFIG = {
    'Palmer': {
        'item_ids': ['aa71ec48-af81-4d87-9bab-04627735c288'],
        'account_map': {
            '535be1c8-5191-4f1f-8591-8d607538a883': 'Checking',
            'feb08f5e-d151-40d4-b816-89647b9b7b19': 'Mastercard Black',
            '22935e0c-0484-46fb-b638-5be4c03d3331': 'Visa Infinite',
        },
    },
    'Rafa': {
        'item_ids': ['8702072c-6224-4f8f-a2be-ba61e4200557'],
        'account_map': {
            'edd1a40e-583c-4e93-ba28-05947f84162f': 'NuBank Conta',
            '66b17a4e-8c15-47f0-abc2-b2425b027a4e': 'NuBank Cartão',
        },
    },
}


def _detect_installment(description):
    """Detect installment from description (e.g. 'STORE 3/12')."""
    m = re.search(r'(\d{1,2})/(\d{1,2})', description)
    if m:
        current = int(m.group(1))
        total = int(m.group(2))
        if 0 < current <= total <= 60:
            return True, m.group(0)
    return False, ''


def _detect_internal_transfer(description, amount, raw_description=''):
    """Detect internal transfers (PIX to self, CC payments, etc.)."""
    desc_lower = description.lower()
    raw_lower = (raw_description or '').lower()
    combined = desc_lower + ' ' + raw_lower
    patterns = [
        'pagamento de fatura',
        'pgto debito conta',
        'transf entre contas',
        'resgate',
        'aplicacao',
        'pag boleto itau unibanco',
        'pag boleto banco itaucard',
        'pag boleto itaucard',
        'pagamento recebido',  # CC payment received (from checking)
    ]
    return any(p in combined for p in patterns)


def _extract_base_desc(description):
    """Remove installment suffix and clean up description."""
    desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', description).strip()
    return desc


def _compute_invoice_month(txn_date, closing_day):
    """
    Compute invoice_month for a CC transaction.

    If the transaction date is before or on the closing day, it goes on
    this month's bill (invoice_month = next month).
    If after closing day, it goes on next month's bill (invoice_month = month+2).
    """
    import calendar
    if txn_date.day <= closing_day:
        # This month's billing cycle -> next month's bill
        if txn_date.month == 12:
            return f'{txn_date.year + 1}-01'
        return f'{txn_date.year}-{txn_date.month + 1:02d}'
    else:
        # Next month's billing cycle -> month after next's bill
        if txn_date.month >= 11:
            year = txn_date.year + (1 if txn_date.month == 12 else 0)
            month = (txn_date.month % 12) + 2
            if month > 12:
                month -= 12
                year += 1
            return f'{year}-{month:02d}'
        return f'{txn_date.year}-{txn_date.month + 2:02d}'


class Command(BaseCommand):
    help = 'Sync transactions from Pluggy Open Finance API'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True, help='Profile name (e.g. Palmer, Rafa)')
        parser.add_argument('--from', dest='from_date', help='Start date YYYY-MM-DD (default: 12 months ago)')
        parser.add_argument('--to', dest='to_date', help='End date YYYY-MM-DD (default: today)')
        parser.add_argument('--accounts', help='Comma-separated account filter: checking,master,nubank')
        parser.add_argument('--item', dest='item_id', help='Override Pluggy item ID (for ad-hoc sync)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without writing')
        parser.add_argument('--save-balance', action='store_true',
                            help='Create BalanceAnchor from current checking balance')

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        # Load credentials
        client_id = os.environ.get('PLUGGY_CLIENT_ID', '')
        client_secret = os.environ.get('PLUGGY_CLIENT_SECRET', '')

        if not all([client_id, client_secret]):
            self.stderr.write(self.style.ERROR(
                'Missing PLUGGY_CLIENT_ID or PLUGGY_CLIENT_SECRET in environment'))
            return

        # Load profile
        profile_name = options['profile']
        try:
            profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Profile "{profile_name}" not found'))
            return

        self.profile = profile
        self.dry_run = options['dry_run']

        # Resolve item IDs and account map for this profile
        config = PROFILE_CONFIG.get(profile_name, {})
        account_map = dict(config.get('account_map', {}))

        if options['item_id']:
            item_ids = [options['item_id']]
        else:
            item_ids = config.get('item_ids', [])
            # Fallback to env var for backwards compatibility
            if not item_ids:
                env_item = os.environ.get('PLUGGY_ITEM_ID', '')
                if env_item:
                    item_ids = [env_item]

        if not item_ids:
            self.stderr.write(self.style.ERROR(
                f'No Pluggy item IDs configured for profile "{profile_name}". '
                f'Use --item or add to PROFILE_CONFIG.'))
            return

        # Date range
        to_date = options['to_date'] or date.today().isoformat()
        from_date = options['from_date'] or (date.today() - timedelta(days=365)).isoformat()

        # Account filter
        account_filter = None
        if options['accounts']:
            account_filter = [a.strip().lower() for a in options['accounts'].split(',')]

        self.stdout.write(f'Pluggy sync: profile={profile.name}, items={len(item_ids)}, '
                          f'from={from_date}, to={to_date}, dry_run={self.dry_run}')

        # Initialize client
        client = PluggyClient(client_id, client_secret)

        # Load Vault accounts
        vault_accounts = {a.name: a for a in Account.objects.filter(profile=profile)}
        self._load_categorization(profile)

        # Ensure external_ids are set on Vault accounts
        for pluggy_id, vault_name in account_map.items():
            if vault_name in vault_accounts:
                acct = vault_accounts[vault_name]
                if acct.external_id != pluggy_id:
                    acct.external_id = pluggy_id
                    if not self.dry_run:
                        acct.save(update_fields=['external_id'])
                    self.stdout.write(f'  Mapped {vault_name} -> {pluggy_id}')

        total_new = 0
        total_skipped = 0
        total_updated = 0

        # Process each Pluggy item
        for item_id in item_ids:
            item = client.get_item(item_id)
            connector_name = item.get('connector', {}).get('name', '?')
            self.stdout.write(f'\n=== Item: {connector_name} ({item_id[:12]}...) '
                              f'status={item.get("status")} ===')

            # Pre-fetch bills for CC accounts in this item
            self.bill_map = {}
            for pluggy_acct_id, vault_name in account_map.items():
                if vault_name not in vault_accounts:
                    continue
                if vault_accounts[vault_name].account_type == 'credit_card':
                    try:
                        bills = client.get_bills(pluggy_acct_id)
                        for bill in bills:
                            due_date = bill['dueDate'][:10]
                            inv_month = due_date[:7]
                            self.bill_map[bill['id']] = inv_month
                        self.stdout.write(f'  Loaded {len(bills)} bills for {vault_name}')
                    except Exception as e:
                        self.stderr.write(f'  Failed to load bills for {vault_name}: {e}')

            # Sync each mapped account in this item
            for pluggy_acct_id, vault_name in account_map.items():
                if account_filter:
                    name_lower = vault_name.lower()
                    if not any(f in name_lower for f in account_filter):
                        continue

                if vault_name not in vault_accounts:
                    self.stdout.write(self.style.WARNING(
                        f'  Vault account "{vault_name}" not found, skipping'))
                    continue

                vault_acct = vault_accounts[vault_name]
                self.stdout.write(f'\n--- {vault_name} ({pluggy_acct_id[:8]}...) ---')

                txns = client.get_transactions(pluggy_acct_id, from_date, to_date)
                self.stdout.write(f'  Pluggy returned {len(txns)} transactions')

                new, skipped, updated = self._sync_transactions(txns, vault_acct)
                total_new += new
                total_skipped += skipped
                total_updated += updated

        # Save checking balance as BalanceAnchor
        if options['save_balance'] and not self.dry_run:
            self._save_balance_anchor(client, vault_accounts, profile, account_map)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {total_new} new, {total_updated} updated, {total_skipped} skipped'))

    def _load_categorization(self, profile):
        """Load rename rules, Pluggy category mappings, and categorization rules."""
        self.rename_rules = list(
            RenameRule.objects.filter(profile=profile, is_active=True)
        )
        # Pluggy category mappings: pluggy_category_id -> (category, subcategory)
        self.pluggy_mappings = {}
        for pm in PluggyCategoryMapping.objects.filter(profile=profile).select_related('category', 'subcategory'):
            self.pluggy_mappings[pm.pluggy_category_id] = (pm.category, pm.subcategory)
        # Categorization rules (pre-loaded, sorted by priority desc)
        from api.models import CategorizationRule, Subcategory
        self.categorization_rules = list(
            CategorizationRule.objects.filter(
                profile=profile, is_active=True
            ).select_related('category', 'subcategory').order_by('-priority')
        )
        # Additional card routing: card_last4 -> Account
        # Purchases on additional cards get routed to their own account
        self.card_account_map = {}
        try:
            rafa_acc = Account.objects.get(profile=profile, name='Mastercard - Rafa')
            self.card_account_map['5780'] = rafa_acc
        except Account.DoesNotExist:
            pass

    def _apply_rename(self, description):
        """Apply rename rules to a description."""
        for rule in self.rename_rules:
            if rule.keyword.lower() in description.lower():
                return rule.display_name
        return description

    def _apply_pluggy_categorization(self, pluggy_category_id, description=''):
        """Resolve Vault category from Pluggy category ID.
        Tries exact match first, then falls back to parent category (first 2 digits + 000000).
        When Pluggy gives parent-level only (no subcategory), tries description-based
        inference and CategorizationRule matching."""
        if not pluggy_category_id:
            return None, None
        result = self.pluggy_mappings.get(pluggy_category_id)
        if not result:
            # Fall back to parent category
            parent_id = pluggy_category_id[:2] + '000000'
            result = self.pluggy_mappings.get(parent_id)
        if not result:
            return None, None

        category, subcategory = result

        # Subcategory refinement: when Pluggy gave parent-level only
        if category and not subcategory and description:
            from api.services import _infer_subcategory_from_description
            inferred = _infer_subcategory_from_description(
                category.name, description, self.profile
            )
            if inferred:
                subcategory = inferred

        # CategorizationRule can override category+subcategory or just refine subcategory
        # Uses pre-loaded rules from _load_categorization() to avoid N+1 queries
        if description and hasattr(self, 'categorization_rules'):
            desc_upper = description.upper()
            for rule in self.categorization_rules:
                if rule.keyword.upper() in desc_upper:
                    if rule.category:
                        category = rule.category
                        subcategory = rule.subcategory
                    elif rule.subcategory and category and rule.subcategory.category_id == category.id:
                        subcategory = rule.subcategory
                    break

        return category, subcategory

    def _sync_transactions(self, pluggy_txns, vault_acct):
        """Sync a list of Pluggy transactions into Vault for one account."""
        new_count = 0
        skipped_count = 0
        updated_count = 0

        # Batch load existing external_ids for this account
        existing_ext_ids = set(
            Transaction.objects.filter(
                account=vault_acct, profile=self.profile
            ).exclude(external_id='').values_list('external_id', flat=True)
        )

        # Load existing transactions for fuzzy dedup against legacy imports.
        # Legacy data has different casing, punctuation, accents, and sometimes
        # dates off by 1 day, so we normalize aggressively.
        def _norm(s):
            nfkd = unicodedata.normalize('NFKD', s)
            ascii_only = nfkd.encode('ASCII', 'ignore').decode()
            return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

        existing_legacy = set()
        existing_legacy_by_key = {}  # key -> (amount, description) for updating
        # Also index by (amount, norm_desc) for date-tolerant matching
        existing_legacy_by_amt = {}  # (abs_amt, norm_desc) -> list of (date, amount, description)
        # Index by (date, abs_amount) for amount-only matching (handles renamed PIX descriptions)
        existing_legacy_by_date_amt = {}  # (date, abs_amt) -> list of (amount, description)
        for t in Transaction.objects.filter(
            account=vault_acct, profile=self.profile, external_id=''
        ).values_list('date', 'amount', 'description'):
            key = (t[0], abs(t[1]), _norm(t[2]))
            existing_legacy.add(key)
            existing_legacy_by_key[key] = (t[1], t[2])
            amt_key = (abs(t[1]), _norm(t[2]))
            existing_legacy_by_amt.setdefault(amt_key, []).append((t[0], t[1], t[2]))
            da_key = (t[0], abs(t[1]))
            existing_legacy_by_date_amt.setdefault(da_key, []).append((t[1], t[2]))

        batch_create = []
        is_cc = vault_acct.account_type == 'credit_card'
        closing_day = vault_acct.closing_day or 25  # Itau default

        for ptxn in pluggy_txns:
            ext_id = ptxn['id']

            # Skip if already synced by external_id
            if ext_id in existing_ext_ids:
                skipped_count += 1
                continue

            # Parse transaction data
            raw_desc = ptxn.get('descriptionRaw') or ptxn.get('description', '')
            description = ptxn.get('description', raw_desc)
            raw_amount = Decimal(str(ptxn['amount']))
            txn_date = date.fromisoformat(ptxn['date'][:10])
            month_str = txn_date.strftime('%Y-%m')

            # Pluggy sign convention:
            #   Checking: negative=debit, positive=credit (matches Vault)
            #   CC: positive=charge, negative=payment (OPPOSITE of Vault)
            # Vault stores CC charges as negative amounts.
            if is_cc:
                amount = -raw_amount
            else:
                amount = raw_amount

            # Fuzzy dedup: match on (date, abs_amount, normalized_description)
            # Handles legacy data with different casing, punctuation, accents
            norm_desc = _norm(description)
            fuzzy_key = (txn_date, abs(amount), norm_desc)
            matched = False
            if fuzzy_key in existing_legacy:
                matched_amount, matched_desc = existing_legacy_by_key[fuzzy_key]
                matched = True
            else:
                # Date-tolerant match (+/- 1 day) for OFX vs bank date differences
                amt_key = (abs(amount), norm_desc)
                for ldate, lamt, ldesc in existing_legacy_by_amt.get(amt_key, []):
                    if abs((txn_date - ldate).days) <= 1:
                        alt_key = (ldate, abs(lamt), _norm(ldesc))
                        if alt_key in existing_legacy:
                            matched_amount, matched_desc = lamt, ldesc
                            fuzzy_key = alt_key
                            txn_date_match = ldate
                            matched = True
                            break

            # Fallback: match on (date, abs_amount) only when there's exactly
            # one legacy txn with that combo. Handles PIX descriptions where
            # legacy OFX uses abbreviated names (e.g. "Antanio02 03") and
            # Pluggy uses full names (e.g. "PIX TRANSF Antônio02/03").
            if not matched:
                da_key = (txn_date, abs(amount))
                candidates = existing_legacy_by_date_amt.get(da_key, [])
                if len(candidates) == 1:
                    matched_amount, matched_desc = candidates[0]
                    fuzzy_key = (txn_date, abs(matched_amount), _norm(matched_desc))
                    if fuzzy_key in existing_legacy:
                        matched = True
                        if self.verbosity >= 2:
                            self.stdout.write(f'  Date+amount dedup: "{matched_desc}" -> "{description}"')

            if matched:
                if not self.dry_run:
                    match_qs = Transaction.objects.filter(
                        account=vault_acct, profile=self.profile,
                        amount=matched_amount,
                        description=matched_desc, external_id='',
                    )
                    first = match_qs.first()
                    if first:
                        update_fields = ['external_id']
                        first.external_id = ext_id
                        # Backfill Pluggy category on existing transactions
                        p_cat = ptxn.get('category') or ''
                        p_cat_id = ptxn.get('categoryId') or ''
                        if p_cat and not first.pluggy_category:
                            first.pluggy_category = p_cat
                            first.pluggy_category_id = p_cat_id
                            update_fields += ['pluggy_category', 'pluggy_category_id']
                            # Also apply Pluggy category if uncategorized
                            if not first.category and not first.is_manually_categorized:
                                cat, sub = self._apply_pluggy_categorization(p_cat_id)
                                if cat:
                                    first.category = cat
                                    first.subcategory = sub
                                    update_fields += ['category', 'subcategory']
                        first.save(update_fields=update_fields)
                updated_count += 1
                existing_ext_ids.add(ext_id)
                existing_legacy.discard(fuzzy_key)
                continue

            # Apply rename rules
            display_desc = self._apply_rename(description)

            # Detect installments
            is_installment, installment_info = _detect_installment(description)

            # CC installment metadata from Pluggy (more reliable than regex)
            cc_meta = ptxn.get('creditCardMetadata')
            if cc_meta and cc_meta.get('totalInstallments'):
                is_installment = True
                inst_num = cc_meta.get('installmentNumber', 1)
                inst_total = cc_meta['totalInstallments']
                installment_info = f'{inst_num}/{inst_total}'
                # Include installment info in display description if not already there
                if not re.search(r'\d+/\d+', display_desc):
                    display_desc = f'{display_desc} {installment_info}'

            # Compute invoice_month for CC transactions
            invoice_month = ''
            if is_cc:
                # Use Pluggy billId if available (exact), else fall back to heuristic
                bill_id = (cc_meta or {}).get('billId', '')
                if bill_id and bill_id in self.bill_map:
                    invoice_month = self.bill_map[bill_id]
                else:
                    invoice_month = _compute_invoice_month(txn_date, closing_day)

            # Detect internal transfers
            is_transfer = _detect_internal_transfer(description, amount, raw_desc)

            # Pluggy category data
            pluggy_category = ptxn.get('category') or ''
            pluggy_category_id = ptxn.get('categoryId') or ''

            # Card last 4 digits from creditCardMetadata
            card_last4 = (cc_meta or {}).get('cardNumber', '') or ''

            # Categorization: Pluggy category mapping + description refinement + rules
            category, subcategory = self._apply_pluggy_categorization(
                pluggy_category_id, description=display_desc
            )

            # Route additional card purchases to their own account
            target_account = vault_acct
            if card_last4 and card_last4 in self.card_account_map:
                target_account = self.card_account_map[card_last4]

            txn = Transaction(
                profile=self.profile,
                date=txn_date,
                description=display_desc,
                description_original=description,
                raw_description=raw_desc,
                amount=amount,
                account=target_account,
                category=category,
                subcategory=subcategory,
                source_file=f'pluggy:{ext_id[:8]}',
                is_installment=is_installment,
                installment_info=installment_info,
                is_recurring=False,
                is_internal_transfer=is_transfer,
                invoice_month=invoice_month,
                month_str=month_str,
                external_id=ext_id,
                pluggy_category=pluggy_category,
                pluggy_category_id=pluggy_category_id,
                card_last4=card_last4,
            )
            batch_create.append(txn)
            new_count += 1

        if batch_create and not self.dry_run:
            Transaction.objects.bulk_create(batch_create, batch_size=500)

        action = 'Would create' if self.dry_run else 'Created'
        self.stdout.write(f'  {action} {new_count} new, updated {updated_count}, skipped {skipped_count}')

        return new_count, skipped_count, updated_count

    def _save_balance_anchor(self, client, vault_accounts, profile, account_map):
        """Save current checking balance as a BalanceAnchor."""
        # Find the checking account in the account map
        checking_pluggy_id = None
        for pluggy_id, vault_name in account_map.items():
            if vault_name in vault_accounts and vault_accounts[vault_name].account_type == 'checking':
                checking_pluggy_id = pluggy_id
                break

        if not checking_pluggy_id:
            self.stdout.write('  No checking account mapped, skipping balance anchor')
            return

        try:
            balance_data = client.get_account_balance(checking_pluggy_id)
            balance = Decimal(str(balance_data['balance']))
            today = date.today()

            anchor, created = BalanceAnchor.objects.update_or_create(
                profile=profile,
                date=today,
                defaults={
                    'balance': balance,
                    'source_file': 'pluggy:checking',
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action} BalanceAnchor: {today} = R$ {balance}')
        except Exception as e:
            self.stderr.write(f'  Failed to save balance anchor: {e}')
