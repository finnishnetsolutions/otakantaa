# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_auto_20151127_0946'),
        ('organization', '0003_organization_activated'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='schemes',
            field=models.ManyToManyField(to='content.Scheme', through='content.SchemeOwner'),
        ),
    ]
