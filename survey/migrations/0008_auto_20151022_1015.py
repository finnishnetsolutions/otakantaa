# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import libs.multilingo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0007_auto_20151021_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveyoption',
            name='text',
            field=libs.multilingo.models.fields.MultilingualTextField(default=None, max_length=255, blank=True, help_text=None, null=True, verbose_name='vaihtoehto'),
        ),
        migrations.AlterField(
            model_name='surveyquestion',
            name='text',
            field=libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='kysymys'),
        ),
        migrations.AlterField(
            model_name='surveysubtitle',
            name='text',
            field=libs.multilingo.models.fields.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='v\xe4liotsikko'),
        ),
    ]
