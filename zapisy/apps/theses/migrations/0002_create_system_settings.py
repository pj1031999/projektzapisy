"""
This migration creates a single instance of models.ThesesSystemSettings;
this is to allow to edit the configuration via the admin interface,
without changing settings.py and restarting the app
"""

from django.db import migrations, models
import django.db.models.deletion
from ..validators import validate_num_required_votes, validate_master_rejecter

DEFAULT_REQUIRED_THESIS_VOTES = 3


def create_thesis_settings(apps, schema_editor):
    ThesesSystemSettings = apps.get_model("theses", "ThesesSystemSettings")
    db_alias = schema_editor.connection.alias
    ThesesSystemSettings.objects.using(db_alias).create(
        num_required_votes=DEFAULT_REQUIRED_THESIS_VOTES
    )


def remove_system_settings(apps, schema_editor):
    ThesesSystemSettings = apps.get_model("theses", "ThesesSystemSettings")
    db_alias = schema_editor.connection.alias
    ThesesSystemSettings.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('theses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThesesSystemSettings',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('num_required_votes', models.SmallIntegerField(validators=[
                 validate_num_required_votes], verbose_name='Liczba głosów wymaganych do zaakceptowania')),
                ('master_rejecter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='users.Employee', validators=[
                 validate_master_rejecter], verbose_name='Członek komisji odpowiedzialny za zwracanie prac do poprawek')),
            ],
            options={
                'verbose_name': 'ustawienia systemu prac dyplomowych',
                'verbose_name_plural': 'ustawienia systemu prac dyplomowych',
            },
        ),
        migrations.RunPython(create_thesis_settings, remove_system_settings)
    ]
