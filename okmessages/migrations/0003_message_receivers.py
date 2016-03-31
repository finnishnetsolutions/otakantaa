# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('okmessages', '0002_auto_20151119_1330'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='receivers',
            field=models.ManyToManyField(related_name='received_messages', verbose_name='vastaanottajat', through='okmessages.Delivery', to=settings.AUTH_USER_MODEL),
        ),
    ]
