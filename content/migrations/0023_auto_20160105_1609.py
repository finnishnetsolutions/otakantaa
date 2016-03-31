# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import otakantaa.models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0022_scheme_twitter_search'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheme',
            name='summary',
            field=otakantaa.models.MultilingualRedactorField(default='', help_text=None, max_length=500, verbose_name='yhteenveto'),
        ),
    ]
