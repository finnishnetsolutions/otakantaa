# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_auto_20151028_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='lead_text',
            field=otakantaa.models.MultilingualRedactorField(default='', help_text=None, verbose_name='ingressi'),
        ),
    ]
