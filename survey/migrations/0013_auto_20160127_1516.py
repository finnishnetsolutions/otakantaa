# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0012_auto_20151229_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyanswer',
            name='text',
            field=models.CharField(max_length=10000, null=True, blank=True),
        ),
    ]
