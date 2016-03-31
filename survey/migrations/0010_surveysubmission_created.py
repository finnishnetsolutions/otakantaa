# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0009_auto_20151119_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveysubmission',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
