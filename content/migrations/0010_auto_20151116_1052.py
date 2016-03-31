# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0009_auto_20151105_1323'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participationdetails',
            options={'ordering': ('-created', 'title')},
        ),
        migrations.AlterField(
            model_name='scheme',
            name='tags',
            field=models.ManyToManyField(to='tagging.Tag', verbose_name='aiheet'),
        ),
    ]
