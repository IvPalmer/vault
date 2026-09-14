"""
Categorize every uncategorized transaction with the smart categorization engine.

Pipeline stage. Until this existed the engine only ran from the "Categorizar"
button on Visão Mensal: sync applied the Pluggy category (plus keyword rules) at
insert time and nothing else, so any charge Pluggy does not classify — most
foreign merchants: Anthropic, Beatport, Bandcamp, Yoyaku — sat uncategorized
until someone clicked. The learned strategies (exact description history,
amount pattern) that would have resolved them never ran unattended.

Runs globally (no month filter): a stranded row is stranded whichever month it
is in. Also runs the installment-series inheritance and inconsistency detection
the engine carries.

--min-confidence defaults to 0.90 here (the button uses the engine's 0.70):
Pluggy (1.0), keyword rules (0.98), Apple-by-amount (0.97) and exact-description
history (0.95) clear it. The amount pattern (0.85: "three earlier charges of
~R$28 on this card were food") and token similarity (≤0.75) do not — a dry run
on 2026-09-13 had the amount pattern file Beatport under Alimentação, a
cannabis shop under Limpeza e Manutenção and Traders Club under Pet Shop. Those
stay for a human, via the button.

Dry-run by default. Pass --apply to write.
"""
from django.core.management.base import BaseCommand

from api.management.commands.sync_pluggy import PROFILE_CONFIG
from api.models import Profile
from api.services import smart_categorize

DEFAULT_MIN_CONFIDENCE = 0.90


class Command(BaseCommand):
    help = 'Categorize uncategorized transactions (pipeline stage; dry-run by default).'

    def add_arguments(self, parser):
        parser.add_argument('--profile', help='Profile name. Default: all in PROFILE_CONFIG.')
        parser.add_argument('--apply', action='store_true', help='Write changes (default: dry-run).')
        parser.add_argument('--month', help='Limit to one YYYY-MM (default: all months).')
        parser.add_argument('--min-confidence', type=float, default=DEFAULT_MIN_CONFIDENCE,
                            help=f'Lowest confidence applied (default {DEFAULT_MIN_CONFIDENCE}).')

    def _profiles(self, arg):
        if arg:
            return Profile.objects.filter(name__iexact=arg)
        return Profile.objects.filter(name__in=list(PROFILE_CONFIG.keys()))

    def handle(self, *args, **opts):
        apply = opts['apply']
        total = 0
        for profile in self._profiles(opts.get('profile')):
            r = smart_categorize(
                month_str=opts.get('month'), dry_run=not apply, profile=profile,
                min_confidence=opts['min_confidence'],
            )
            total += r['categorized'] + r.get('subcategorized', 0)
            self.stdout.write(
                f'{profile.name}: {r["categorized"]}/{r["total_uncategorized"]} '
                f'categorized, {r.get("subcategorized", 0)} subcategorized {r["by_strategy"]}, '
                f'{r["installment_reconciled"]} installment positions reconciled'
            )
            for d in r['details']:
                sub = f' / {d["new_subcategory"]}' if d['new_subcategory'] else ''
                self.stdout.write(
                    f'  {d["month_str"]} {d["description"][:40]:40} {d["amount"]:>10.2f}'
                    f' -> {d["new_category"]}{sub} [{d["method"]} {d["confidence"]}]'
                )
            left = r['total_uncategorized'] - r['categorized']
            if left:
                self.stdout.write(self.style.WARNING(
                    f'  {left} still uncategorized (below {opts["min_confidence"]} or no signal)'))
        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nTotal categorized: {total}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run. {total} would be categorized. Re-run with --apply.'))
