# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('content', '0002_auto_20150925_0942'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParticipationDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='otsikko')),
                ('description', otakantaa.models.MultilingualRedactorField(default='', help_text=None, verbose_name='kuvaus', blank=True)),
                ('status', models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Avoin'), (6, 'P\xe4\xe4ttynyt')])),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('opened', models.DateTimeField(auto_now=True)),
                ('closed', models.DateTimeField(default=None, null=True, blank=True)),
                ('expiration_date', models.DateField(verbose_name='P\xe4\xe4ttymisp\xe4iv\xe4')),
                ('type', models.SmallIntegerField(default=None, choices=[(0, 'Keskustelu'), (1, 'Kysely')])),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('scheme', models.ForeignKey(to='content.Scheme')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='participation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='participation',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='participation',
            name='scheme',
        ),
        migrations.DeleteModel(
            name='Participation',
        ),
        migrations.AlterUniqueTogether(
            name='participationdetails',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
