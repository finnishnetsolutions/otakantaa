# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_scheme_lead_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheme',
            name='description',
            field=otakantaa.models.MultilingualRedactorField(default='', help_text=None, verbose_name='lis\xe4tieto', blank=True),
        ),
        migrations.AlterField(
            model_name='scheme',
            name='lead_text',
            field=otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=500, verbose_name='ingressi'),
        ),
    ]
