# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conversation', '0007_comment_admin_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]
