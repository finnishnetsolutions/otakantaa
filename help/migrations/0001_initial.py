# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import libs.multilingo.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Instruction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='Otsikko')),
                ('description', libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, verbose_name='Sis\xe4lt\xf6')),
                ('connect_link_type', models.CharField(null=True, default=None, choices=[(None, 'ei mit\xe4\xe4n'), ('privacy-policy', 'rekisteriseloste'), ('contact-details', 'yhteystiedot')], max_length=50, blank=True, unique=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='help.Instruction', null=True)),
            ],
            options={
                'verbose_name': 'Ohje',
                'verbose_name_plural': 'Ohjeet',
            },
        ),
    ]
