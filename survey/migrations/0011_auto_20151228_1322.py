# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20151215_1221'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('survey', '0010_surveysubmission_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveySubmitter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submitter_id', models.CharField(unique=True, max_length=32)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.OneToOneField(related_name='survey_submitter', null=True, default=None, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='surveysubmission',
            name='client_identifier',
            field=models.ForeignKey(to='account.ClientIdentifier', null=True),
        ),
        migrations.AddField(
            model_name='surveysubmission',
            name='submitter',
            field=models.ForeignKey(to='survey.SurveySubmitter', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='surveysubmission',
            unique_together=set([('survey', 'submitter')]),
        ),
        migrations.RemoveField(
            model_name='surveysubmission',
            name='user',
        ),
    ]
