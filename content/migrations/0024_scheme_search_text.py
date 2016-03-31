# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0023_auto_20160105_1609'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='search_text',
            field=models.TextField(default=None, null=True),
        ),
    ]
