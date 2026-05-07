import uuid
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from api.models import Profile, RecurringMapping, Transaction
from api.services import _normalize_transaction_description as normalize_description


def dedupe_description_key(description):
    """Use the same normalization as services._normalize_transaction_description.

    Pluggy noise prefixes (PIX TRANSF, PAG BOLETO, etc.) are stripped so
    legacy CSV format and Pluggy verbose format collapse to the same key.
    """
    return normalize_description(description)


def keep_score(txn):
    linked_count = txn.recurring_mapping_links.count() + txn.cross_month_links.count()
    if txn.recurring_mappings.exists():
        linked_count += 1
    return (
        linked_count,
        1 if txn.is_manually_categorized else 0,
        1 if (txn.source_file or '').startswith('pluggy:') else 0,
        1 if txn.external_id else 0,
        1 if txn.pluggy_category_id else 0,
        txn.created_at,
    )


class Command(BaseCommand):
    help = 'Find and optionally delete known phantom duplicate transactions.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name or UUID. Defaults to all profiles.')
        parser.add_argument('--apply', action='store_true', help='Delete duplicate rows. Omit for dry-run.')
        parser.add_argument('--dry-run', action='store_true', help='Preview duplicates without deleting rows.')
        parser.add_argument('--database', default='default', help='Database alias to use.')

    def _profiles(self, profile_arg):
        qs = Profile.objects.using(self.db_alias).all()
        if not profile_arg:
            return qs
        by_name = qs.filter(name__iexact=profile_arg)
        if by_name.exists():
            return by_name
        try:
            return qs.filter(id=uuid.UUID(profile_arg))
        except ValueError:
            return qs.none()

    def _find_groups(self, profile):
        """
        Find phantom Pluggy/legacy duplicate pairs.

        Bucket by (account, abs(amount), normalized_description) — date is
        intentionally omitted from the bucket because Pluggy posts the bank-
        side date while legacy CSV imports use the user-side date, and the
        two can differ by a day for the same real charge (e.g. consórcio
        cotas: legacy 05/02, Pluggy 06/02).

        Within each bucket, pair Pluggy rows with legacy rows greedily by
        closest date. A pair is a phantom only when:
          - One side is pluggy: source_file
          - Other side is non-pluggy
          - Dates differ by at most 1 day

        Same-source rows (two pluggy or two legacy) are NEVER paired —
        they are presumed legitimate distinct payments.

        Skip groups whose normalized description is too short (< 4 chars) to
        avoid over-matching generic descriptions like "IOF" or "Compra".
        """
        buckets = defaultdict(list)
        txns = Transaction.objects.using(self.db_alias).filter(profile=profile).select_related('account').order_by(
            'account_id', 'amount', 'date', 'created_at'
        )
        for txn in txns:
            desc_key = dedupe_description_key(txn.description)
            if len(desc_key) < 4:
                continue
            key = (txn.account_id, abs(txn.amount), desc_key)
            buckets[key].append(txn)

        groups = []
        for rows in buckets.values():
            if len(rows) < 2:
                continue
            pluggy = sorted(
                [r for r in rows if (r.source_file or '').startswith('pluggy:')],
                key=lambda r: r.date,
            )
            legacy = sorted(
                [r for r in rows if not (r.source_file or '').startswith('pluggy:')],
                key=lambda r: r.date,
            )
            if not pluggy or not legacy:
                continue
            # Greedy pair Pluggy↔legacy by closest date within ±1 day
            unmatched_legacy = list(legacy)
            for p in pluggy:
                for l in unmatched_legacy:
                    if abs((p.date - l.date).days) <= 1:
                        groups.append([p, l])
                        unmatched_legacy.remove(l)
                        break
        return groups

    def _transfer_links(self, delete_txn, keep_txn):
        RecurringMapping.objects.using(self.db_alias).filter(transaction=delete_txn).update(transaction=keep_txn)
        for mapping in delete_txn.recurring_mapping_links.all():
            mapping.transactions.add(keep_txn)
        for mapping in delete_txn.cross_month_links.all():
            mapping.cross_month_transactions.add(keep_txn)

    def _resolve_group(self, group):
        """
        Decide which rows to keep and which to delete in a phantom group.

        Phantom groups always have at least one Pluggy and at least one legacy
        row (enforced by _find_groups). Real count = max(len(pluggy), len(legacy)).
        Keep the larger side intact; delete the smaller side. Pluggy wins ties
        because its rows carry richer metadata (external_id, pluggy_category,
        bill linkage).
        """
        pluggy_rows = [r for r in group if (r.source_file or '').startswith('pluggy:')]
        legacy_rows = [r for r in group if not (r.source_file or '').startswith('pluggy:')]
        if len(pluggy_rows) >= len(legacy_rows):
            keep_rows, delete_rows = pluggy_rows, legacy_rows
        else:
            keep_rows, delete_rows = legacy_rows, pluggy_rows
        # Pick the best-ranked surviving row to inherit links from delete rows
        link_target = sorted(keep_rows, key=keep_score, reverse=True)[0]
        return link_target, delete_rows

    def handle(self, *args, **options):
        apply = options['apply']
        self.db_alias = options['database']
        profiles = list(self._profiles(options.get('profile')))
        if not profiles:
            self.stderr.write(self.style.ERROR('No matching profile found'))
            return

        grand_total = 0
        for profile in profiles:
            groups = self._find_groups(profile)
            delete_ids = []
            self.stdout.write(f'\nProfile: {profile.name}')
            for group in groups:
                link_target, delete_rows = self._resolve_group(group)
                if not delete_rows:
                    continue
                delete_ids.extend(txn.id for txn in delete_rows)
                total_amount = sum(abs(txn.amount) for txn in delete_rows)
                self.stdout.write(
                    f'  {link_target.date} {link_target.account.name} {link_target.description[:60]} '
                    f'R${abs(link_target.amount)}: keep {link_target.id}, delete {len(delete_rows)} '
                    f'(phantom R${total_amount})'
                )
            self.stdout.write(f'  Total duplicate rows: {len(delete_ids)}')
            grand_total += len(delete_ids)

            if apply and delete_ids:
                with db_transaction.atomic(using=self.db_alias):
                    for group in groups:
                        link_target, delete_rows = self._resolve_group(group)
                        for duplicate in delete_rows:
                            self._transfer_links(duplicate, link_target)
                            duplicate.delete()
                self.stdout.write(self.style.SUCCESS(f'  Deleted {len(delete_ids)} rows'))

        if not apply:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run only. Re-run with --apply to delete {grand_total} duplicate rows.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDeleted {grand_total} duplicate rows total.'))
