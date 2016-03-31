# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0017_auto_20151201_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='summary',
            field=otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=500, verbose_name='yhteenveto'),
        ),
    ]
