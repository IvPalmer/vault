import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_seed_bank_templates'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetupTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('template_data', models.JSONField(default=dict, help_text='Full wizard state snapshot')),
                ('is_builtin', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(
                    blank=True, null=True,
                    help_text='Owner profile. Null for global templates.',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='setup_templates',
                    to='api.profile',
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
    ]
