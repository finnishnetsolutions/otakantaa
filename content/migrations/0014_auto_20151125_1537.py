# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0013_remove_scheme_temp_owners'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='schemeowner',
            unique_together=set([('scheme', 'user', 'organization')]),
        ),
    ]
