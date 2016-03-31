# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0021_scheme_premoderation'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='twitter_search',
            field=models.CharField(max_length=255, verbose_name='Twitter-hakusana', blank=True),
        ),
    ]
