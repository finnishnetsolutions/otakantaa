# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_auto_20151127_0946'),
        ('account', '0003_default_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='schemes',
            field=models.ManyToManyField(to='content.Scheme', through='content.SchemeOwner'),
        ),
    ]
