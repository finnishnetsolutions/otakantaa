# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0019_auto_20151202_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheme',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Julkaistu'), (6, 'P\xe4\xe4ttynyt')]),
        ),
        migrations.AlterField(
            model_name='scheme',
            name='visibility',
            field=models.SmallIntegerField(default=1, verbose_name='n\xe4kyvyys', choices=[(1, 'Luonnos'), (10, 'Julkinen'), (8, 'Arkistoitu')]),
        ),
    ]
