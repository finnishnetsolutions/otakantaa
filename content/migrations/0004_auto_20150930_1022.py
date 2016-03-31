# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_auto_20150928_0718'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participationdetails',
            name='type',
        ),
        migrations.AlterField(
            model_name='participationdetails',
            name='scheme',
            field=models.ForeignKey(related_name='participations', to='content.Scheme'),
        ),
    ]
