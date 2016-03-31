# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_auto_20151104_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participationdetails',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Avoin')]),
        ),
    ]
