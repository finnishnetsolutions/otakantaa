# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import libs.multilingo.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, max_length=50, verbose_name='nimi')),
            ],
            options={
                'verbose_name': 'Aihe',
                'verbose_name_plural': 'Aiheet',
            },
        ),
    ]
