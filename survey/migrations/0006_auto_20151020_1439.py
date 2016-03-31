# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_auto_20151019_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='show_results',
            field=models.SmallIntegerField(null=True),
        ),
    ]
