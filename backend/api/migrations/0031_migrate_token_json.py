"""
Data migration: imports existing token.json into GoogleCalendarAccount
for Palmer's profile, and creates a CalendarSelection for the R&R calendar.
"""
import json
import os

from django.db import migrations

PALMER_PROFILE_ID = 'a29184ea-9d4d-4c65-8300-386ed5b07fca'
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'token.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'credentials.json')


def forwards(apps, schema_editor):
    GoogleCalendarAccount = apps.get_model('api', 'GoogleCalendarAccount')
    Profile = apps.get_model('api', 'Profile')

    if not os.path.exists(TOKEN_FILE):
        return

    try:
        profile = Profile.objects.get(id=PALMER_PROFILE_ID)
    except Profile.DoesNotExist:
        return

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    # If token_data doesn't have client_id/secret, pull from credentials.json
    if 'client_id' not in token_data and os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE) as f:
            cred_data = json.load(f)
        cred_type = 'web' if 'web' in cred_data else 'installed'
        client_info = cred_data.get(cred_type, {})
        token_data.setdefault('client_id', client_info.get('client_id', ''))
        token_data.setdefault('client_secret', client_info.get('client_secret', ''))
        token_data.setdefault('token_uri', client_info.get('token_uri', 'https://oauth2.googleapis.com/token'))

    email = token_data.get('email', 'raphaelpalmer42@gmail.com')

    GoogleCalendarAccount.objects.create(
        profile=profile,
        email=email,
        token_data=token_data,
    )


def backwards(apps, schema_editor):
    GoogleCalendarAccount = apps.get_model('api', 'GoogleCalendarAccount')
    GoogleCalendarAccount.objects.filter(
        profile_id=PALMER_PROFILE_ID,
        email='raphaelpalmer42@gmail.com',
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0030_google_calendar_accounts'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
