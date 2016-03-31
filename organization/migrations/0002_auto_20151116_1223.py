# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='municipalities',
            field=models.ManyToManyField(related_name='organizations', verbose_name='Kunnat', to='fimunicipality.Municipality'),
        ),
    ]
