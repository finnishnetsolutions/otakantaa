# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_auto_20150930_1022'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participationdetails',
            options={'ordering': ('-created',)},
        ),
    ]
