# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_auto_20151116_1223'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='activated',
            field=models.DateTimeField(default=None, verbose_name='aktivoitu', null=True),
        ),
    ]
