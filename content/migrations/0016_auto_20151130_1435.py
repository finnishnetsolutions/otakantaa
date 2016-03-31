# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_auto_20151127_0946'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schemeowner',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='Hyv\xe4ksy kutsu', choices=[(True, 'Kyll\xe4'), (False, 'Ei')]),
        ),
        migrations.AlterField(
            model_name='schemeowner',
            name='organization',
            field=models.ForeignKey(related_name='owned_schemes', to='organization.Organization', null=True),
        ),
        migrations.AlterField(
            model_name='schemeowner',
            name='user',
            field=models.ForeignKey(related_name='owned_schemes', to=settings.AUTH_USER_MODEL),
        ),
    ]
