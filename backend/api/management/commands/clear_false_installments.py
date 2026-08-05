"""
Clear is_installment on rows that are not credit-card purchases.

A purchase can only be split into positions on a card. On a checking account
the bank glues the transaction's own day/month onto a truncated description —
'PIX TRANSF ASSOCIA05/05' dated 2026-05-05 — and the N/M regex in sync_pluggy
read that as position 5 of 5. 83 PIX rows on Palmer's Checking carried
is_installment=True that way, polluting the installment tables.

sync_pluggy now gates detection on the account type, so this is a one-off
repair of rows ingested before that fix. Idempotent: re-running finds nothing.
Only the two installment flags are touched — amount, category, invoice_month
and every other field are left exactly as they are.

Dry-run by default. Pass --apply to write.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as dbtx

from api.models import Profile, Transaction


class Command(BaseCommand):
    help = 'Clear is_installment on non credit-card rows (misparsed dates)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the changes (default: dry-run)')
        parser.add_argument('--profile', help='Limit to one profile name')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        verbosity = options.get('verbosity', 1)

        qs = Transaction.objects.filter(is_installment=True).exclude(
            account__account_type='credit_card'
        ).select_related('account', 'profile')
        if options.get('profile'):
            # Fail loud on a typo — a silent "0 rows" would read as "already clean".
            if not Profile.objects.filter(name=options['profile']).exists():
                raise CommandError(f'Perfil desconhecido: {options["profile"]!r}')
            qs = qs.filter(profile__name=options['profile'])

        rows = list(qs.order_by('date'))
        if not rows:
            self.stdout.write(self.style.SUCCESS(
                'Nenhuma parcela falsa fora de cartão de crédito.'))
            return

        by_account = {}
        for t in rows:
            key = (t.profile.name if t.profile else '-',
                   t.account.name, t.account.account_type)
            by_account[key] = by_account.get(key, 0) + 1

        self.stdout.write(f'{len(rows)} linhas marcadas como parcela fora de cartão:')
        for (prof, acct, acct_type), n in sorted(by_account.items()):
            self.stdout.write(f'  {prof} / {acct} ({acct_type}): {n}')

        if verbosity >= 2:
            for t in rows:
                self.stdout.write(
                    f'    {t.date} {t.amount:>10} info={t.installment_info!r} '
                    f'{t.description!r}')

        if not apply_changes:
            self.stdout.write(self.style.WARNING(
                'Dry-run. Rode com --apply para limpar.'))
            return

        with dbtx.atomic():
            updated = Transaction.objects.filter(
                id__in=[t.id for t in rows]
            ).update(is_installment=False, installment_info='')

        self.stdout.write(self.style.SUCCESS(f'{updated} linhas limpas.'))
