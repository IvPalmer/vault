"""
Run the daily finance pipeline as ONE sequenced, guarded invocation.

    sync Palmer → sync Rafa → rebucket → dedup → phantom check → audit

This replaces five independent cron lines that fired on the clock at 08:00,
08:15, 08:20, 08:30 and 08:35. Runtime is ~5s against 15-minute gaps, so
*duration* was never the risk: the risk is that `rebucket --apply` and
`dedup --apply` ran regardless of whether the syncs finished, or finished at
all. Rebucketing and DELETING on top of a failed or partial sync is a
different failure class from running late, and a fixed gap does not protect
against it.

Design notes, each of which exists because of a specific failure:

* **Sequential calls, fail-closed.** Control flow *is* the dependency; no
  per-stage authorisation records are needed for five synchronous steps.
* **Child processes with a hard timeout.** In-process `call_command` is not
  reliably killable, so a hung stage would hang the run.
* **A checker finding something is NOT a stage failure.** Both checkers exit
  non-zero by design. Treating that as failure would stop the run before the
  audit and the report — the exact opposite of the point.
* **The report runs in a `finally`**, with whatever was gathered.
* **`--strict` coverage on every network-dependent stage.** All three swallow
  bill-fetch failures and continue, and partial bill coverage changes which
  row counts as bill-backed and therefore which one dedup keeps.
* **Non-blocking advisory lock**, so a second invocation exits immediately
  rather than queueing behind a hung one.
* **The maintenance gate is a row, not a lock** — an advisory lock dies with
  the connection, which would let the next scheduled run mutate rows a human
  was still reviewing.
* **The run row is created BEFORE the first stage**, so a crash leaves an
  unfinished record for missed-run detection to find.
"""
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from api.models import FinancePipelineRun

# Any bigint; the pair identifies this particular pipeline across the database.
LOCK_KEY = 8_143_207_001

# Beyond this, upstream data is stale enough that mutating on top of it is not
# obviously safe, so the mutating stages go dry and the run asks for approval.
DEFAULT_GAP_HOURS = 36


class Command(BaseCommand):
    help = 'Run the daily finance pipeline as one guarded, sequenced invocation.'

    def add_arguments(self, parser):
        parser.add_argument('--kind', default='scheduled',
                            choices=[k for k, _ in FinancePipelineRun.KIND_CHOICES])
        parser.add_argument('--dry-run', action='store_true',
                            help='Run the mutating stages without applying.')
        parser.add_argument('--timeout', type=int, default=600,
                            help='Per-stage hard timeout in seconds (default 600).')
        parser.add_argument('--gap-hours', type=int, default=DEFAULT_GAP_HOURS,
                            help=f'Staleness threshold (default {DEFAULT_GAP_HOURS}h).')
        parser.add_argument('--approve-gap-run', metavar='RUN_ID',
                            help='Approve a catch-up dry run so the next run may apply.')

    # ---- locking -------------------------------------------------------

    def _try_lock(self):
        with connection.cursor() as cur:
            cur.execute('SELECT pg_try_advisory_lock(%s)', [LOCK_KEY])
            return cur.fetchone()[0]

    def _unlock(self):
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_unlock(%s)', [LOCK_KEY])

    # ---- gates ---------------------------------------------------------

    @staticmethod
    def maintenance_open():
        """An unfinished maintenance row IS the gate. Deliberately not a lock:
        a lock is released the moment the maintenance command disconnects."""
        return FinancePipelineRun.objects.filter(
            kind='maintenance', finished_at__isnull=True).first()

    @staticmethod
    def last_applied_run():
        return FinancePipelineRun.objects.filter(
            finished_at__isnull=False, applied=True,
        ).exclude(kind='maintenance').order_by('-finished_at').first()

    def gap_blocks_apply(self, gap_hours):
        """True when upstream is stale enough that we should not mutate blind.

        Terminates: a clean catch-up dry run is approvable, and an approved run
        lets the NEXT invocation apply against freshly synced data — an old
        mutation plan is never replayed.
        """
        last = self.last_applied_run()
        if last is None:
            return False                     # first ever run: nothing to be stale about
        age = timezone.now() - last.finished_at
        if age.total_seconds() <= gap_hours * 3600:
            return False
        approved = FinancePipelineRun.objects.filter(
            approved_at__isnull=False, finished_at__gt=last.finished_at,
        ).exists()
        return not approved

    # ---- stages --------------------------------------------------------

    def _run_stage(self, name, argv, timeout, checker=False):
        """Run one stage as a child process.

        Returns (outcome, detail). `outcome` is 'ok' | 'findings' | 'failed' |
        'timeout'. A checker exiting non-zero means it FOUND something, which
        is information, not a broken stage.
        """
        cmd = [sys.executable, 'manage.py'] + argv
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 'timeout', f'excedeu {timeout}s'
        tail = (r.stdout or '')[-1500:] + (r.stderr or '')[-1500:]
        if r.returncode == 0:
            return 'ok', tail
        return ('findings' if checker else 'failed'), tail

    # ---- main ----------------------------------------------------------

    def handle(self, *args, **opts):
        if opts.get('approve_gap_run'):
            n = FinancePipelineRun.objects.filter(
                id=opts['approve_gap_run'], finished_at__isnull=False,
                approved_at__isnull=True,
            ).update(approved_at=timezone.now())
            if n:
                self.stdout.write(self.style.SUCCESS(
                    'Execução aprovada. A próxima rodada pode aplicar.'))
            else:
                self.stderr.write(self.style.ERROR(
                    'Execução não encontrada, não terminada, ou já aprovada.'))
                sys.exit(1)
            return

        gate = self.maintenance_open()
        if gate:
            self.stdout.write(self.style.WARNING(
                f'Janela de manutenção aberta desde {gate.started_at:%d/%m %H:%M} '
                f'— pulando as etapas que alteram dados.'))

        if not self._try_lock():
            self.stdout.write(self.style.WARNING(
                'Pipeline já em execução — saindo sem fazer nada.'))
            return

        timeout = opts['timeout']
        stale = self.gap_blocks_apply(opts['gap_hours'])
        apply = not opts['dry_run'] and gate is None and not stale
        if stale:
            self.stdout.write(self.style.WARNING(
                'Última aplicação está velha demais — etapas de alteração vão '
                'em dry-run. Revise e libere com --approve-gap-run <id>.'))

        run = FinancePipelineRun.objects.create(
            kind=opts['kind'], applied=apply,
            scheduled_for=timezone.now() if opts['kind'] == 'scheduled' else None,
        )
        stages, failed = {}, False
        try:
            plan = [
                ('sync_palmer', ['sync_pluggy', '--profile', 'Palmer',
                                 '--save-balance', '--strict'], False, True),
                ('sync_rafa', ['sync_pluggy', '--profile', 'Rafa',
                               '--save-balance', '--strict'], False, True),
                ('rebucket', ['rebucket_invoice_month', '--strict']
                             + (['--apply'] if apply else []), False, True),
                ('dedup', ['dedup_installments', '--strict']
                          + (['--apply'] if apply else []), False, True),
                ('phantom', ['check_phantom_duplicates', '--max-rows', '5',
                             '--max-value', '500'], True, False),
                ('audit', ['audit_sync'], True, False),
            ]
            for name, argv, is_checker, mutating in plan:
                if failed and mutating:
                    stages[name] = {'outcome': 'skipped',
                                    'detail': 'etapa anterior falhou'}
                    continue
                if gate and mutating and name.startswith(('rebucket', 'dedup')):
                    stages[name] = {'outcome': 'skipped', 'detail': 'manutenção'}
                    continue
                outcome, detail = self._run_stage(name, argv, timeout, checker=is_checker)
                stages[name] = {'outcome': outcome, 'detail': detail[-800:]}
                self.stdout.write(f'  {name:14} {outcome}')
                if outcome in ('failed', 'timeout'):
                    failed = True
        finally:
            # The report always runs, with whatever was gathered. A checker
            # finding something must never prevent the summary.
            run.finished_at = timezone.now()
            run.stages = stages
            run.applied = apply and not failed
            run.save(update_fields=['finished_at', 'stages', 'applied'])
            self._unlock()
            self._report(run, stages, failed, apply)

        if failed:
            sys.exit(1)

    def _report(self, run, stages, failed, apply):
        self.stdout.write('')
        self.stdout.write(f'run {run.id} | {run.kind} | '
                          f'{"aplicado" if run.applied else "dry-run"}')
        for name, s in stages.items():
            style = {
                'ok': self.style.SUCCESS, 'findings': self.style.WARNING,
                'skipped': self.style.WARNING,
            }.get(s['outcome'], self.style.ERROR)
            self.stdout.write(style(f'  {name:14} {s["outcome"]}'))
        missed = FinancePipelineRun.objects.filter(
            kind='scheduled', finished_at__isnull=True,
        ).exclude(id=run.id).count()
        if missed:
            self.stdout.write(self.style.ERROR(
                f'  {missed} execução(ões) agendada(s) sem término registrado — '
                f'o pipeline morreu no meio em algum momento.'))
        if failed:
            self.stdout.write(self.style.ERROR('pipeline FALHOU'))
