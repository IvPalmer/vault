"""
Set (or update) a checking BalanceAnchor for a specific date.

Pluggy's daily sync stamps anchors with the SYNC date, which lags the real
bank balance by ~1-2 days. At a month boundary that skews the next month's
opening balance (`_get_checking_balance_eom` trusts the anchor date). When that
happens, take the authoritative end-of-month "SALDO DO DIA" from the bank
statement and drop an exact anchor here — `_get_checking_balance_eom` then uses
it directly (exact anchor on month-end). The daily Pluggy sync stamps
current-date anchors, so a manual month-end anchor is never overwritten.

Usage:
    python manage.py set_balance_anchor --profile Palmer --date 2026-05-31 --balance 21996.44
    python manage.py set_balance_anchor --profile Palmer --date 2026-05-31 --balance 21996.44 --dry-run
"""

from datetime import date as _date
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from api.models import BalanceAnchor, Profile


class Command(BaseCommand):
    help = 'Set/update a checking BalanceAnchor for a date (e.g. month-end from a bank statement).'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True, help='Profile name (e.g. Palmer)')
        parser.add_argument('--date', required=True, help='Anchor date YYYY-MM-DD')
        parser.add_argument('--balance', required=True, help='Balance in BRL, e.g. 21996.44')
        parser.add_argument('--source', default='statement:manual',
                            help="source_file tag (default 'statement:manual')")
        parser.add_argument('--dry-run', action='store_true', help='Show change without saving')

    def handle(self, *args, **options):
        try:
            profile = Profile.objects.get(name=options['profile'])
        except Profile.DoesNotExist:
            raise CommandError(f"Profile '{options['profile']}' not found")
        try:
            anchor_date = _date.fromisoformat(options['date'])
        except ValueError:
            raise CommandError(f"Invalid --date '{options['date']}' (use YYYY-MM-DD)")
        try:
            balance = Decimal(str(options['balance']))
        except (InvalidOperation, ValueError):
            raise CommandError(f"Invalid --balance '{options['balance']}'")

        existing = BalanceAnchor.objects.filter(profile=profile, date=anchor_date).first()
        old = existing.balance if existing else None
        self.stdout.write(
            f"{profile.name} {anchor_date}: {old if old is not None else '(none)'} -> {balance}")

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE('dry-run — nothing saved'))
            return

        if existing:
            existing.balance = balance
            existing.source_file = options['source']
            existing.save(update_fields=['balance', 'source_file'])
            self.stdout.write(self.style.SUCCESS('Updated existing anchor.'))
        else:
            BalanceAnchor.objects.create(
                profile=profile, date=anchor_date, balance=balance,
                source_file=options['source'])
            self.stdout.write(self.style.SUCCESS('Created anchor.'))
