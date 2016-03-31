# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('okmessages', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('read', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterModelOptions(
            name='feedback',
            options={'verbose_name': 'palaute', 'verbose_name_plural': 'palautteet'},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('-sent',), 'verbose_name': 'viesti', 'verbose_name_plural': 'viestit'},
        ),
        migrations.RemoveField(
            model_name='message',
            name='deleted_by',
        ),
        migrations.RemoveField(
            model_name='message',
            name='from_moderator',
        ),
        migrations.RemoveField(
            model_name='message',
            name='read_by',
        ),
        migrations.RemoveField(
            model_name='message',
            name='receivers',
        ),
        migrations.RemoveField(
            model_name='message',
            name='to_moderator',
        ),
        migrations.RemoveField(
            model_name='message',
            name='warning',
        ),
        migrations.AlterField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(related_name='sent_messages', on_delete=django.db.models.deletion.SET_NULL, verbose_name='l\xe4hett\xe4j\xe4', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='delivery',
            name='message',
            field=models.ForeignKey(related_name='deliveries', to='okmessages.Message'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='receiver',
            field=models.ForeignKey(related_name='message_deliveries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='delivery',
            unique_together=set([('message', 'receiver')]),
        ),
    ]
