# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import survey.models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0011_auto_20151228_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveysubmitter',
            name='submitter_id',
            field=models.CharField(default=survey.models.create_submitter_id, unique=True, max_length=32),
        ),
    ]
