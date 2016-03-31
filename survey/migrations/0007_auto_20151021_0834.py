# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0006_auto_20151020_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='show_results',
            field=models.SmallIntegerField(null=True, verbose_name='Vastausten n\xe4ytt\xe4minen'),
        ),
    ]
