# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0012_auto_20151123_1453'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheme',
            name='temp_owners',
        ),
    ]
