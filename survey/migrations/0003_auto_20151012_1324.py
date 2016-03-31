# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20151009_1056'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyquestion',
            name='required',
            field=models.BooleanField(default=0, verbose_name='pakollinen'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='surveyquestion',
            name='type',
            field=models.IntegerField(choices=[(1, 'Yhden valinta'), (2, 'Useamman valinta'), (3, 'Tekstikentt\xe4'), (4, 'Numerokentt\xe4')]),
        ),
    ]
