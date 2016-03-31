# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0007_auto_20151030_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheme',
            name='lead_text',
            field=otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=500, verbose_name='tiivistelm\xe4'),
        ),
    ]
