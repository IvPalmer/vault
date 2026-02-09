"""
Restore user-created data (RecurringTemplate, RecurringMapping, BudgetConfig)
from a JSON backup file.

Usage:
    python manage.py db_restore                          # default: backups/vault_backup.json
    python manage.py db_restore --input my.json          # custom path
    python manage.py db_restore --clear                  # clear existing before restore
    python manage.py db_restore --profile Palmer         # restore only Palmer's data
"""
import json
import os
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import (
    Profile,
    RecurringTemplate, RecurringMapping, BudgetConfig,
    Category, Transaction,
)


class Command(BaseCommand):
    help = 'Restore RecurringTemplate, RecurringMapping, and BudgetConfig from JSON backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            default=None,
            help='Input file path (default: backups/vault_backup.json)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing RecurringMapping and BudgetConfig before restore (scoped to profile)',
        )
        parser.add_argument(
            '--profile',
            default=None,
            help='Profile name to restore data for. If backup contains profile_name, '
                 'only matching records are restored. If not specified, restores all.',
        )

    def handle(self, *args, **options):
        input_path = options['input']
        if not input_path:
            # /app in Docker maps to ./backend on host
            backup_dir = os.path.join('/app', 'backups')
            if not os.path.exists('/app'):
                # Running outside Docker
                backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups')
            backup_dir = os.path.abspath(backup_dir)
            input_path = os.path.join(backup_dir, 'vault_backup.json')

        if not os.path.exists(input_path):
            self.stdout.write(self.style.ERROR(f'Backup file not found: {input_path}'))
            return

        with open(input_path) as f:
            data = json.load(f)

        self.stdout.write(f'Restoring from: {input_path}')
        self.stdout.write(f'Exported at: {data.get("exported_at", "unknown")}')

        # Resolve profile
        profile_name = options.get('profile')
        profile = None
        if profile_name:
            try:
                profile = Profile.objects.get(name=profile_name)
                self.stdout.write(f'Restoring for profile: {profile.name} ({profile.id})')
            except Profile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Profile "{profile_name}" not found'))
                return

        if options['clear']:
            self.stdout.write('Clearing existing mappings and configs...')
            qs_map = RecurringMapping.objects.all()
            qs_cfg = BudgetConfig.objects.all()
            if profile:
                qs_map = qs_map.filter(profile=profile)
                qs_cfg = qs_cfg.filter(profile=profile)
            qs_map.delete()
            qs_cfg.delete()

        # --- Restore RecurringTemplate ---
        tpl_created = 0
        tpl_existed = 0
        # Build name→obj map for FK resolution in mappings
        tpl_name_to_obj = {}
        for t in data.get('recurring_templates', []):
            # If backup has profile_name and we're filtering, skip non-matching
            if profile and t.get('profile_name') and t['profile_name'] != profile.name:
                continue

            # Determine which profile to assign
            tpl_profile = profile
            if not tpl_profile and t.get('profile_name'):
                tpl_profile = Profile.objects.filter(name=t['profile_name']).first()

            lookup = {'name': t['name']}
            if tpl_profile:
                lookup['profile'] = tpl_profile

            defaults = {
                'template_type': t['template_type'],
                'default_limit': Decimal(t['default_limit']),
                'due_day': t.get('due_day'),
                'is_active': t.get('is_active', True),
                'display_order': t.get('display_order', 0),
            }
            if tpl_profile:
                defaults['profile'] = tpl_profile

            obj, created = RecurringTemplate.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
            tpl_name_to_obj[t['name']] = obj
            if created:
                tpl_created += 1
            else:
                tpl_existed += 1
        self.stdout.write(f'  Templates: {tpl_created} created, {tpl_existed} existed')

        # Build lookup maps for FK resolution (scoped to profile if specified)
        cat_qs = Category.objects.all()
        if profile:
            cat_qs = cat_qs.filter(profile=profile)
        cat_name_map = {c.name: c for c in cat_qs}

        # --- Restore RecurringMapping ---
        map_created = 0
        map_skipped = 0
        for m in data.get('recurring_mappings', []):
            # If backup has profile_name and we're filtering, skip non-matching
            if profile and m.get('profile_name') and m['profile_name'] != profile.name:
                map_skipped += 1
                continue

            # Determine profile for this mapping
            map_profile = profile
            if not map_profile and m.get('profile_name'):
                map_profile = Profile.objects.filter(name=m['profile_name']).first()

            # Resolve template FK by name (UUIDs change across DB rebuilds)
            template = None
            if m.get('template_name'):
                template = tpl_name_to_obj.get(m['template_name'])
            if not template and not m.get('is_custom'):
                self.stdout.write(self.style.WARNING(
                    f'  SKIP mapping: template "{m.get("template_name")}" not found'
                ))
                map_skipped += 1
                continue

            # Resolve category FK by name
            category = None
            if m.get('category_name'):
                category = cat_name_map.get(m['category_name'])

            # Check for existing (template + month_str + profile uniqueness)
            if template:
                exists_qs = RecurringMapping.objects.filter(
                    template=template, month_str=m['month_str']
                )
                if map_profile:
                    exists_qs = exists_qs.filter(profile=map_profile)
                if exists_qs.exists():
                    map_skipped += 1
                    continue

            create_kwargs = {
                'template': template,
                'category': category,
                'match_mode': m.get('match_mode', 'manual'),
                'month_str': m['month_str'],
                'status': m.get('status', 'missing'),
                'expected_amount': Decimal(m.get('expected_amount', '0')),
                'actual_amount': Decimal(m['actual_amount']) if m.get('actual_amount') else None,
                'notes': m.get('notes', ''),
                'is_custom': m.get('is_custom', False),
                'custom_name': m.get('custom_name', ''),
                'custom_type': m.get('custom_type', ''),
                'display_order': m.get('display_order', 0),
            }
            if map_profile:
                create_kwargs['profile'] = map_profile

            mapping = RecurringMapping.objects.create(**create_kwargs)

            # Re-link transactions by UUID if they still exist
            if m.get('transaction_ids'):
                existing_txns = Transaction.objects.filter(
                    id__in=m['transaction_ids']
                ).values_list('id', flat=True)
                if existing_txns:
                    mapping.transactions.set(existing_txns)

            if m.get('cross_month_transaction_ids'):
                existing_cross = Transaction.objects.filter(
                    id__in=m['cross_month_transaction_ids']
                ).values_list('id', flat=True)
                if existing_cross:
                    mapping.cross_month_transactions.set(existing_cross)

            map_created += 1

        self.stdout.write(f'  Mappings: {map_created} created, {map_skipped} skipped')

        # --- Restore BudgetConfig ---
        cfg_created = 0
        cfg_skipped = 0
        for b in data.get('budget_configs', []):
            # If backup has profile_name and we're filtering, skip non-matching
            if profile and b.get('profile_name') and b['profile_name'] != profile.name:
                cfg_skipped += 1
                continue

            # Determine profile for this config
            cfg_profile = profile
            if not cfg_profile and b.get('profile_name'):
                cfg_profile = Profile.objects.filter(name=b['profile_name']).first()

            template = None
            if b.get('template_name'):
                template = tpl_name_to_obj.get(b['template_name'])

            category = None
            if b.get('category_name'):
                category = cat_name_map.get(b['category_name'])

            if not template and not category:
                cfg_skipped += 1
                continue

            lookup = {
                'template': template,
                'category': category,
                'month_str': b['month_str'],
            }
            if cfg_profile:
                lookup['profile'] = cfg_profile

            defaults = {
                'limit_override': Decimal(b['limit_override']),
            }
            if cfg_profile:
                defaults['profile'] = cfg_profile

            _, created = BudgetConfig.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
            if created:
                cfg_created += 1
            else:
                cfg_skipped += 1

        self.stdout.write(f'  Configs: {cfg_created} created, {cfg_skipped} skipped')
        self.stdout.write(self.style.SUCCESS('Restore complete!'))
