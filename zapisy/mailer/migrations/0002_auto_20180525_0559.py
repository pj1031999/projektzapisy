# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-05-25 05:59
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dontsendentry',
            name='to_address',
            field=models.CharField(max_length=50, verbose_name='adres'),
        ),
        migrations.AlterField(
            model_name='dontsendentry',
            name='when_added',
            field=models.DateTimeField(verbose_name='od kiedy'),
        ),
        migrations.AlterField(
            model_name='message',
            name='from_address',
            field=models.CharField(max_length=50, verbose_name='nadawca'),
        ),
        migrations.AlterField(
            model_name='message',
            name='message_body',
            field=models.TextField(verbose_name='treść'),
        ),
        migrations.AlterField(
            model_name='message',
            name='message_body_html',
            field=models.TextField(blank=True, verbose_name='treść html'),
        ),
        migrations.AlterField(
            model_name='message',
            name='priority',
            field=models.CharField(choices=[('1', 'wysoki'), ('2', 'średni'), ('3', 'niski'), ('4', 'odroczona')], default='2', max_length=1, verbose_name='priorytet'),
        ),
        migrations.AlterField(
            model_name='message',
            name='subject',
            field=models.CharField(max_length=100, verbose_name='temat'),
        ),
        migrations.AlterField(
            model_name='message',
            name='to_address',
            field=models.CharField(max_length=50, verbose_name='odbiorca'),
        ),
        migrations.AlterField(
            model_name='message',
            name='when_added',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='dodano'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='from_address',
            field=models.CharField(max_length=50, verbose_name='nadawca'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='log_message',
            field=models.TextField(verbose_name='wiadomość'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='message_body',
            field=models.TextField(verbose_name='treść'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='message_body_html',
            field=models.TextField(blank=True, verbose_name='treść html'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='priority',
            field=models.CharField(choices=[('1', 'wysoki'), ('2', 'średni'), ('3', 'niski'), ('4', 'odroczona')], max_length=1, verbose_name='priorytet'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='result',
            field=models.CharField(choices=[('1', 'sukces'), ('2', 'nie wysłane'), ('3', 'niepowodzenie')], max_length=1, verbose_name='wynik'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='subject',
            field=models.CharField(max_length=100, verbose_name='temat'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='to_address',
            field=models.CharField(max_length=50, verbose_name='odbiorca'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='when_added',
            field=models.DateTimeField(verbose_name='dodano'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='when_attempted',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='czas próby'),
        ),
    ]
