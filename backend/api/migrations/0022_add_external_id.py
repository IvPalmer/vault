from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_add_salary_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='external_id',
            field=models.CharField(max_length=200, blank=True, default='', db_index=True),
        ),
        migrations.AddField(
            model_name='account',
            name='external_id',
            field=models.CharField(max_length=200, blank=True, default='',
                                   help_text='External account ID (e.g. Pluggy account UUID)'),
        ),
    ]
