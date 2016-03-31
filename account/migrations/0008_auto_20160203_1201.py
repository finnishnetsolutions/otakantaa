# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_auto_20160127_1511'),
        ('organization', '0006_adminsettings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='organizations',
        ),
        migrations.AddField(
            model_name='user',
            name='organizations',
            field=models.ManyToManyField(related_name='admins', through='organization.AdminSettings', to='organization.Organization'),
        ),
    ]
