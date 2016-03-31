# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20151019_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyanswer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='survey.SurveyQuestion'),
        ),
    ]
