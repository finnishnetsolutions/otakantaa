# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SurveyElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False, db_index=True)),
                ('text', models.CharField(max_length=255, null=True, verbose_name='vaihtoehto', blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='answer',
            name='option',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='submission',
        ),
        migrations.RemoveField(
            model_name='option',
            name='question',
        ),
        migrations.RemoveField(
            model_name='question',
            name='survey',
        ),
        migrations.AddField(
            model_name='survey',
            name='show_results',
            field=models.SmallIntegerField(default=2),
        ),
        migrations.AlterField(
            model_name='surveysubmission',
            name='survey',
            field=models.ForeignKey(related_name='submissions', to='survey.Survey'),
        ),
        migrations.CreateModel(
            name='SurveyPage',
            fields=[
                ('surveyelement_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.SurveyElement')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.surveyelement',),
        ),
        migrations.CreateModel(
            name='SurveyQuestion',
            fields=[
                ('surveyelement_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.SurveyElement')),
                ('text', models.CharField(max_length=255, verbose_name='kysymys')),
                ('type', models.IntegerField(choices=[(1, 'Yhden monivalinta'), (2, 'Useamman monivalinta'), (3, 'Tekstikentt\xe4'), (4, 'Numerokentt\xe4')])),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.surveyelement',),
        ),
        migrations.CreateModel(
            name='SurveySubtitle',
            fields=[
                ('surveyelement_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.SurveyElement')),
                ('text', models.CharField(max_length=255, verbose_name='v\xe4liotsikko')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.surveyelement',),
        ),
        migrations.DeleteModel(
            name='Answer',
        ),
        migrations.DeleteModel(
            name='Option',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
        migrations.AddField(
            model_name='surveyelement',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_survey.surveyelement_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='surveyelement',
            name='survey',
            field=models.ForeignKey(related_name='elements', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='option',
            field=models.ForeignKey(related_name='answers', to='survey.SurveyOption'),
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='submission',
            field=models.ForeignKey(related_name='answers', to='survey.SurveySubmission'),
        ),
        migrations.AddField(
            model_name='surveyoption',
            name='question',
            field=models.ForeignKey(related_name='options', to='survey.SurveyQuestion'),
        ),
    ]
