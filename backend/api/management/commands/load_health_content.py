"""
Load a per-profile health content blob into the DB.

These payloads are real medical records. They are NOT in this repo — the repo
is public, and anything imported by the frontend gets compiled into the SPA
bundle, which nginx serves before any app-level auth runs. They live in the
gitignored private-data/ dir and are loaded from there.

Usage:
    python manage.py load_health_content --profile Rafa --slug glucose_log \
        --file private-data/rafa-glucose_log.json
    python manage.py load_health_content --profile Rafa --slug glucose_log \
        --file <path> --dry-run

    # load every private-data/<profile>-<slug>.json in one go:
    python manage.py load_health_content --profile Rafa --dir private-data/
"""
import json
import os
import glob

from django.core.management.base import BaseCommand, CommandError

from api.models import HealthContent, Profile

VALID_SLUGS = {s for s, _ in HealthContent.SLUG_CHOICES}


class Command(BaseCommand):
    help = 'Load health content JSON into HealthContent rows'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True, help='Profile name (e.g. Rafa)')
        parser.add_argument('--slug', help=f'One of: {", ".join(sorted(VALID_SLUGS))}')
        parser.add_argument('--file', help='Path to the payload JSON')
        parser.add_argument('--dir', help='Load every <profile>-<slug>.json in this dir')
        parser.add_argument('--dry-run', action='store_true', help='Report without writing')

    def handle(self, *args, **options):
        if not options['dir'] and not (options['slug'] and options['file']):
            raise CommandError('Give either --dir, or both --slug and --file')

        profile_name = options['profile']
        try:
            profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist:
            raise CommandError(f'Profile "{profile_name}" not found')

        if options['dir']:
            pattern = os.path.join(options['dir'], f'{profile_name.lower()}-*.json')
            paths = sorted(glob.glob(pattern))
            if not paths:
                raise CommandError(f'No files matching {pattern}')
            items = []
            for p in paths:
                slug = os.path.basename(p)[len(profile_name) + 1:-len('.json')]
                items.append((slug, p))
        else:
            items = [(options['slug'], options['file'])]

        for slug, path in items:
            if slug not in VALID_SLUGS:
                raise CommandError(
                    f'Unknown slug "{slug}" (from {path}). Valid: {", ".join(sorted(VALID_SLUGS))}')
            try:
                with open(path) as fh:
                    payload = json.load(fh)
            except OSError as exc:
                raise CommandError(f'Cannot read {path}: {exc}')
            except ValueError as exc:
                raise CommandError(f'{path} is not valid JSON: {exc}')

            size = len(json.dumps(payload))
            if options['dry_run']:
                self.stdout.write(f'[dry-run] {profile_name}/{slug}: {size} bytes from {path}')
                continue

            obj, created = HealthContent.objects.update_or_create(
                profile=profile, slug=slug, defaults={'payload': payload},
            )
            verb = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(
                f'{verb} {profile_name}/{slug} ({size} bytes)'))
