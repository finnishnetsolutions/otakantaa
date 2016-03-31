# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models, migrations


def set_answer_questions(apps, schema_editor):
    SurveyAnswer = apps.get_model("survey", "SurveyAnswer")

    for answer in SurveyAnswer.objects.filter(question=None):
        answer.question = answer.option.question
        answer.save()


def reveresable_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_auto_20151012_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyanswer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='survey.SurveyQuestion', null=True),
        ),
        migrations.AlterField(
            model_name='surveyanswer',
            name='option',
            field=models.ForeignKey(related_name='answers', to='survey.SurveyOption', null=True),
        ),
        migrations.RunPython(set_answer_questions, reveresable_func),
    ]
