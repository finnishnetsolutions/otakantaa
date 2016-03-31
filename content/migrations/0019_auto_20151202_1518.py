# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0018_scheme_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='closed',
            field=models.DateTimeField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='scheme',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Avoin'), (6, 'P\xe4\xe4ttynyt')]),
        ),
    ]
