# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0014_auto_20151125_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schemeowner',
            name='organization',
            field=models.ForeignKey(to='organization.Organization', null=True),
        ),
        migrations.AlterField(
            model_name='schemeowner',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
