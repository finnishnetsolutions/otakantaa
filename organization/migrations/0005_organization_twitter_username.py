# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_organization_schemes'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='twitter_username',
            field=models.CharField(max_length=255, verbose_name='Twitter-k\xe4ytt\xe4j\xe4nimi', blank=True),
        ),
    ]
