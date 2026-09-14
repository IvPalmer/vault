"""
Link this month's (and last month's) recurring items to their transactions.

Pipeline stage. Until this existed the matcher only ran from the "⚡ Auto-link"
button on Controle, so fixos paid days ago stayed "Faltando" until someone
clicked — and the matcher itself linked by amount, which got 4 of 6 links
wrong on September/2026 data (see api.services.auto_link_recurring).

Runs the current month and the previous one: a charge that lands late (card-
billed insurances on the 26th-28th, a bill paid after the turn of the month)
belongs to the month it was made in. Only items with no linked transaction are
touched, so re-running is idempotent. Category-mode items are not linked
(their actual is the category sum).

Dry-run by default. Pass --apply to write.
"""
from datetime import date

from django.core.management.base import BaseCommand

from api.management.commands.sync_pluggy import PROFILE_CONFIG
from api.models import Profile
from api.services import _month_str_add, auto_link_recurring, initialize_month


class Command(BaseCommand):
    help = 'Auto-link recurring items to transactions (pipeline stage; dry-run by default).'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name. Default: all in PROFILE_CONFIG.')
        parser.add_argument('--apply', action='store_true', help='Write changes (default: dry-run).')
        parser.add_argument('--month', help='Only this YYYY-MM (default: current and previous month).')

    def _profiles(self, arg):
        if arg:
            return Profile.objects.filter(name__iexact=arg)
        return Profile.objects.filter(name__in=list(PROFILE_CONFIG.keys()))

    def handle(self, *args, **opts):
        apply = opts['apply']
        if opts.get('month'):
            months = [opts['month']]
        else:
            current = date.today().strftime('%Y-%m')
            months = [_month_str_add(current, -1), current]
        total = 0
        for profile in self._profiles(opts.get('profile')):
            for month in months:
                if apply:
                    # Idempotent: creates the month's mapping rows only if absent.
                    initialize_month(month, profile=profile)
                r = auto_link_recurring(month, profile=profile, dry_run=not apply)
                total += r['linked']
                self.stdout.write(
                    f'{profile.name} {month}: {r["linked"]}/{r["total_unlinked"]} unlinked items linked')
                for d in r['details']:
                    for t in d['linked']:
                        self.stdout.write(
                            f'  {d["name"][:24]:24} <- {t["description"][:40]:40} {t["amount"]:>10.2f}')
        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nTotal linked: {total}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run. {total} items would be linked. Re-run with --apply.'))
