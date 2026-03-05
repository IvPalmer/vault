"""
Management command to sync transactions from Pluggy Open Finance API.

Usage:
    python manage.py sync_pluggy --profile Palmer
    python manage.py sync_pluggy --profile Palmer --from 2024-01-01 --to 2026-03-04
    python manage.py sync_pluggy --profile Palmer --accounts checking,master
    python manage.py sync_pluggy --profile Palmer --dry-run
"""

import os
import re
import logging
import unicodedata
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import (
    Account, BalanceAnchor, Category, CategorizationRule,
    Profile, RenameRule, Transaction,
)
from api.pluggy import PluggyClient

logger = logging.getLogger(__name__)

# Pluggy account ID -> Vault account name mapping.
# Configured per-profile. Only Palmer's Itau accounts for now.
ACCOUNT_MAP = {
    '535be1c8-5191-4f1f-8591-8d607538a883': 'Checking',
    'feb08f5e-d151-40d4-b816-89647b9b7b19': 'Mastercard Black',
    '22935e0c-0484-46fb-b638-5be4c03d3331': 'Visa Infinite',
    # Savings and Investment excluded — not tracked in Vault currently
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
        parser.add_argument('--profile', required=True, help='Profile name (e.g. Palmer)')
        parser.add_argument('--from', dest='from_date', help='Start date YYYY-MM-DD (default: 12 months ago)')
        parser.add_argument('--to', dest='to_date', help='End date YYYY-MM-DD (default: today)')
        parser.add_argument('--accounts', help='Comma-separated account filter: checking,master,visa')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without writing')
        parser.add_argument('--save-balance', action='store_true',
                            help='Create BalanceAnchor from current checking balance')

    def handle(self, *args, **options):
        # Load credentials
        client_id = os.environ.get('PLUGGY_CLIENT_ID', '')
        client_secret = os.environ.get('PLUGGY_CLIENT_SECRET', '')
        item_id = os.environ.get('PLUGGY_ITEM_ID', '')

        if not all([client_id, client_secret, item_id]):
            self.stderr.write(self.style.ERROR(
                'Missing PLUGGY_CLIENT_ID, PLUGGY_CLIENT_SECRET, or PLUGGY_ITEM_ID in environment'))
            return

        # Load profile
        try:
            profile = Profile.objects.get(name=options['profile'])
        except Profile.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Profile "{options["profile"]}" not found'))
            return

        self.profile = profile
        self.dry_run = options['dry_run']

        # Date range
        to_date = options['to_date'] or date.today().isoformat()
        from_date = options['from_date'] or (date.today() - timedelta(days=365)).isoformat()

        # Account filter
        account_filter = None
        if options['accounts']:
            account_filter = [a.strip().lower() for a in options['accounts'].split(',')]

        self.stdout.write(f'Pluggy sync: profile={profile.name}, '
                          f'from={from_date}, to={to_date}, dry_run={self.dry_run}')

        # Initialize client
        client = PluggyClient(client_id, client_secret)

        # Check item status
        item = client.get_item(item_id)
        self.stdout.write(f'Item status: {item.get("status")} (last sync: {item.get("lastUpdatedAt")})')

        # Load Vault accounts and build mapping
        vault_accounts = {a.name: a for a in Account.objects.filter(profile=profile)}
        self._load_categorization(profile)

        # Ensure external_ids are set on Vault accounts
        for pluggy_id, vault_name in ACCOUNT_MAP.items():
            if vault_name in vault_accounts:
                acct = vault_accounts[vault_name]
                if acct.external_id != pluggy_id:
                    acct.external_id = pluggy_id
                    if not self.dry_run:
                        acct.save(update_fields=['external_id'])
                    self.stdout.write(f'  Mapped {vault_name} -> {pluggy_id}')

        # Sync each mapped account
        total_new = 0
        total_skipped = 0
        total_updated = 0

        # Pre-fetch bills for CC accounts to build billId -> invoice_month map
        self.bill_map = {}  # billId -> invoice_month (YYYY-MM)
        for pluggy_acct_id, vault_name in ACCOUNT_MAP.items():
            if vault_name not in vault_accounts:
                continue
            if vault_accounts[vault_name].account_type == 'credit_card':
                try:
                    bills = client.get_bills(pluggy_acct_id)
                    for bill in bills:
                        due_date = bill['dueDate'][:10]  # YYYY-MM-DD
                        inv_month = due_date[:7]  # YYYY-MM
                        self.bill_map[bill['id']] = inv_month
                    self.stdout.write(f'  Loaded {len(bills)} bills for {vault_name}')
                except Exception as e:
                    self.stderr.write(f'  Failed to load bills for {vault_name}: {e}')

        for pluggy_acct_id, vault_name in ACCOUNT_MAP.items():
            # Apply account filter
            if account_filter:
                name_lower = vault_name.lower()
                if not any(f in name_lower for f in account_filter):
                    continue

            if vault_name not in vault_accounts:
                self.stdout.write(self.style.WARNING(f'  Vault account "{vault_name}" not found, skipping'))
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
            self._save_balance_anchor(client, vault_accounts, profile)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {total_new} new, {total_updated} updated, {total_skipped} skipped'))

    def _load_categorization(self, profile):
        """Load categorization and rename rules for this profile."""
        self.cat_rules = list(
            CategorizationRule.objects.filter(profile=profile, is_active=True)
            .select_related('category', 'subcategory')
            .order_by('-priority')
        )
        self.rename_rules = list(
            RenameRule.objects.filter(profile=profile, is_active=True)
        )
        self.categories = {c.name: c for c in Category.objects.filter(profile=profile)}

    def _apply_rename(self, description):
        """Apply rename rules to a description."""
        for rule in self.rename_rules:
            if rule.keyword.lower() in description.lower():
                return rule.display_name
        return description

    def _apply_categorization(self, description):
        """Apply categorization rules. Returns (category, subcategory) or (None, None)."""
        desc_lower = description.lower()
        for rule in self.cat_rules:
            if rule.keyword.lower() in desc_lower:
                return rule.category, rule.subcategory
        return None, None

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
        for t in Transaction.objects.filter(
            account=vault_acct, profile=self.profile, external_id=''
        ).values_list('date', 'amount', 'description'):
            key = (t[0], abs(t[1]), _norm(t[2]))
            existing_legacy.add(key)
            existing_legacy_by_key[key] = (t[1], t[2])
            amt_key = (abs(t[1]), _norm(t[2]))
            existing_legacy_by_amt.setdefault(amt_key, []).append((t[0], t[1], t[2]))

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

            if matched:
                if not self.dry_run:
                    match_qs = Transaction.objects.filter(
                        account=vault_acct, profile=self.profile,
                        amount=matched_amount,
                        description=matched_desc, external_id='',
                    )
                    first = match_qs.first()
                    if first:
                        first.external_id = ext_id
                        first.save(update_fields=['external_id'])
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

            # Apply categorization rules
            category, subcategory = self._apply_categorization(display_desc)

            txn = Transaction(
                profile=self.profile,
                date=txn_date,
                description=display_desc,
                description_original=description,
                raw_description=raw_desc,
                amount=amount,
                account=vault_acct,
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
            )
            batch_create.append(txn)
            new_count += 1

        if batch_create and not self.dry_run:
            Transaction.objects.bulk_create(batch_create, batch_size=500)

        action = 'Would create' if self.dry_run else 'Created'
        self.stdout.write(f'  {action} {new_count} new, updated {updated_count}, skipped {skipped_count}')

        return new_count, skipped_count, updated_count

    def _save_balance_anchor(self, client, vault_accounts, profile):
        """Save current checking balance as a BalanceAnchor."""
        checking_pluggy_id = '535be1c8-5191-4f1f-8591-8d607538a883'
        if 'Checking' not in vault_accounts:
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
