"""
Resolve a quarantined bill-reconciliation conflict.

`sync_pluggy` refuses to overwrite a stored invoice amount with a disagreeing
Pluggy total and records the disagreement instead. This is how a human closes it.

    manage.py resolve_bill_conflict --list
    manage.py resolve_bill_conflict --id <uuid> --accept-pluggy
    manage.py resolve_bill_conflict --id <uuid> --keep-statement --note "PDF 05/08"

Both resolutions are COMPARE-AND-SWAP: they apply only if the world still looks
the way it did when the conflict was recorded. Otherwise an operator could
resolve a stale conflict over a newer manual edit and silently write the wrong
number.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as dbtx
from django.utils import timezone

from api.models import BillReconciliationConflict, RecurringMapping


class Command(BaseCommand):
    help = 'Resolve a bill-reconciliation conflict (accept Pluggy, or keep the statement).'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='List pending conflicts.')
        parser.add_argument('--id', help='Conflict id to resolve.')
        parser.add_argument('--accept-pluggy', action='store_true',
                            help="Write Pluggy's total into the mapping.")
        parser.add_argument('--keep-statement', action='store_true',
                            help='Keep the stored total; acknowledge the conflict.')
        parser.add_argument('--note', default='', help='Why — e.g. the statement reference.')

    def handle(self, *args, **opts):
        if opts['list'] or not opts.get('id'):
            rows = BillReconciliationConflict.objects.filter(
                resolution='pending').order_by('month_str')
            if not rows:
                self.stdout.write(self.style.SUCCESS('Nenhum conflito pendente.'))
                return
            for c in rows:
                self.stdout.write(
                    f'{c.id}  {c.profile.name:8} {c.card_name:18} {c.month_str}  '
                    f'guardado R$ {c.stored_total:>10} != Pluggy R$ {c.pluggy_total:>10}  '
                    f'(fatura {c.bill_id[:8]}, fecha {c.bill_closing_date})')
            self.stdout.write('\nResolva com --id <uuid> --accept-pluggy | --keep-statement')
            return

        if opts['accept_pluggy'] == opts['keep_statement']:
            raise CommandError('Escolha exatamente um: --accept-pluggy ou --keep-statement.')

        with dbtx.atomic():
            try:
                c = BillReconciliationConflict.objects.select_for_update().get(id=opts['id'])
            except BillReconciliationConflict.DoesNotExist:
                raise CommandError('Conflito não encontrado.')
            if c.resolution != 'pending':
                raise CommandError(f'Conflito já resolvido como "{c.resolution}".')

            mapping = (RecurringMapping.objects.select_for_update().get(id=c.mapping_id)
                       if c.mapping_id else None)
            if mapping is None:
                raise CommandError(
                    'O mapeamento foi apagado; nada a atualizar. '
                    'Feche o conflito manualmente se ele não faz mais sentido.')

            # Compare-and-swap: the stored amount must still be what the conflict
            # described. If someone edited it since, this conflict is stale and a
            # new one already describes the current disagreement.
            if mapping.expected_amount != c.stored_total:
                raise CommandError(
                    f'O valor guardado mudou desde o conflito '
                    f'({c.stored_total} -> {mapping.expected_amount}). '
                    f'Este conflito está obsoleto; revise o mais recente.')

            if opts['accept_pluggy']:
                RecurringMapping.objects.filter(id=mapping.id).update(
                    expected_amount=c.pluggy_total)
                c.resolution = 'accepted_pluggy'
                msg = (f'{c.card_name} {c.month_str}: '
                       f'R$ {c.stored_total} -> R$ {c.pluggy_total} (Pluggy)')
            else:
                c.resolution = 'kept_statement'
                msg = (f'{c.card_name} {c.month_str}: mantido R$ {c.stored_total} '
                       f'(extrato); Pluggy dizia R$ {c.pluggy_total}')

            c.resolved_at = timezone.now()
            if opts['note']:
                c.note = opts['note']
            c.save(update_fields=['resolution', 'resolved_at', 'note'])

        self.stdout.write(self.style.SUCCESS(msg))
