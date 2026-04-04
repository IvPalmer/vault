import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_pessoal_models'),
    ]

    operations = [
        # Rename the model (preserves table data)
        migrations.RenameModel(
            old_name='GoogleCalendarAccount',
            new_name='GoogleAccount',
        ),
        # Update the related_name on the profile FK
        migrations.AlterField(
            model_name='googleaccount',
            name='profile',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='google_accounts',
                to='api.profile',
            ),
        ),
        # Add the new authorized_scopes field
        migrations.AddField(
            model_name='googleaccount',
            name='authorized_scopes',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of OAuth scopes this account has authorized',
            ),
        ),
        # Update the FK on CalendarSelection to point to renamed model
        migrations.AlterField(
            model_name='calendarselection',
            name='account',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='selections',
                to='api.googleaccount',
            ),
        ),
    ]
