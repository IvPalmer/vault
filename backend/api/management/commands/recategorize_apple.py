"""
Re-categorize brandless Apple subscription charges by amount.

The bank never names the Apple service — every subscription arrives as
"APPLECOMBILL" / "Apple Services". This command resolves each brandless Apple
charge to its real service using the amount→service classifier learned from the
profile's reconciled (brand-named) history, then fixes the description,
category, and subcategory. Manually-categorized transactions are left untouched.

Usage:
    python manage.py recategorize_apple --profile Palmer [--dry-run]
"""

from django.core.management.base import BaseCommand

from api.models import Profile, Transaction
from api.services import (
    build_apple_amount_map,
    resolve_apple_subscription,
    _is_generic_apple,
)


class Command(BaseCommand):
    help = 'Re-categorize brandless Apple charges by amount from reconciled history.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True, help='Profile name (e.g. Palmer)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Show changes without saving')

    def handle(self, *args, **options):
        try:
            profile = Profile.objects.get(name=options['profile'])
        except Profile.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Profile '{options['profile']}' not found"))
            return

        dry_run = options['dry_run']
        self.verbosity = options['verbosity']
        amount_map = build_apple_amount_map(profile)
        self.stdout.write(
            f'Learned {len(amount_map)} amount→service mappings from reconciled history.')

        # Brandless Apple subscription charges (incl. the legacy "Apple"→Software
        # noise). Manual overrides are sacrosanct.
        qs = Transaction.objects.filter(
            profile=profile,
            description__icontains='apple',
            is_manually_categorized=False,
        ).select_related('category', 'subcategory').order_by('date')

        changed = 0
        skipped_generic = 0
        examined = 0
        for txn in qs:
            if not _is_generic_apple(txn.description):
                continue
            examined += 1
            hit = resolve_apple_subscription(profile, txn.amount, amount_map)
            if not hit:
                skipped_generic += 1
                continue
            old = (txn.description, txn.category_id,
                   txn.subcategory_id)
            new_cat = hit['category']
            new_sub = hit['subcategory']
            new = (hit['description'], new_cat.id if new_cat else None,
                   new_sub.id if new_sub else None)
            if old == new:
                continue
            changed += 1
            if self.verbosity >= 1:
                old_sub = txn.subcategory.name if txn.subcategory else None
                new_sub_name = new_sub.name if new_sub else None
                self.stdout.write(
                    f'  {txn.date} R${txn.amount} "{txn.description}" '
                    f'[{old_sub}] → "{hit["description"]}" [{new_sub_name}]')
            if not dry_run:
                txn.description = hit['description']
                txn.category = new_cat
                txn.subcategory = new_sub
                txn.save(update_fields=['description', 'category', 'subcategory'])

        action = 'Would change' if dry_run else 'Changed'
        self.stdout.write(self.style.SUCCESS(
            f'\n{action} {changed} txns. '
            f'({examined} brandless Apple examined, '
            f'{skipped_generic} kept generic — no amount match.)'))
