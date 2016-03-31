# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conversation', '0002_auto_20151019_0841'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='quote',
        ),
        migrations.AddField(
            model_name='comment',
            name='quote',
            field=models.ForeignKey(related_name='quoted', blank=True, to='conversation.Comment', null=True),
        ),
    ]
