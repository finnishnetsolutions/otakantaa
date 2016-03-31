# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0020_auto_20151207_0938'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='premoderation',
            field=models.BooleanField(default=False, verbose_name='kommenttien esimoderointi'),
        ),
    ]
