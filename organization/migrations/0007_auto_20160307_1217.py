# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_adminsettings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adminsettings',
            options={'verbose_name': 'yhteyshenkil\xf6', 'verbose_name_plural': 'yhteyshenkil\xf6t'},
        ),
    ]
