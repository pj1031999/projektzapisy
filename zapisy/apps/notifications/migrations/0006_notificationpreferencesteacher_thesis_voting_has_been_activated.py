# Generated by Django 2.1.13 on 2020-02-27 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20190929_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationpreferencesteacher',
            name='thesis_voting_has_been_activated',
            field=models.BooleanField(default=True, verbose_name='Powiadomienie o głosowaniu na pracę dyplomową (dotyczy Komisji Prac Dyplomowych)'),
        ),
    ]
