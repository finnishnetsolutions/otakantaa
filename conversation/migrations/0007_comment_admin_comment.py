# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conversation', '0006_auto_20151029_1028'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='admin_comment',
            field=models.BooleanField(default=False),
        ),
    ]
