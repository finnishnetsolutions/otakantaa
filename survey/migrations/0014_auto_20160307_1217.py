# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_auto_20160127_1516'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyquestion',
            name='type',
            field=models.IntegerField(choices=[(1, 'Yksivalinta'), (2, 'Monivalinta'), (3, 'Tekstikentt\xe4'), (4, 'Numerokentt\xe4')]),
        ),
    ]
