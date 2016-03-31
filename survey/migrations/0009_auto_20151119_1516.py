# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import libs.multilingo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0008_auto_20151022_1015'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyquestion',
            name='instruction_text',
            field=libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, max_length=800, verbose_name='ohjeteksti', blank=True),
        ),
        migrations.AlterField(
            model_name='surveyanswer',
            name='text',
            field=models.CharField(max_length=4000, null=True, blank=True),
        ),
    ]
