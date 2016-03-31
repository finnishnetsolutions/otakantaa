# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=255, verbose_name='aihe')),
                ('message', models.CharField(max_length=4000, verbose_name='viesti')),
                ('sent', models.DateTimeField(default=django.utils.timezone.now)),
                ('warning', models.BooleanField(default=False, verbose_name='Varoitusviesti')),
                ('to_moderator', models.BooleanField(default=False)),
                ('from_moderator', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Viesti',
                'verbose_name_plural': 'Viestit',
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('message_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='okmessages.Message')),
                ('name', models.CharField(max_length=50, verbose_name='nimi', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='s\xe4hk\xf6posti', blank=True)),
            ],
            options={
                'verbose_name': 'Palaute',
                'verbose_name_plural': 'Palautteet',
            },
            bases=('okmessages.message',),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_okmessages.message_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='receivers',
            field=models.ManyToManyField(related_name='received_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='reply_to',
            field=models.ForeignKey(related_name='replies', on_delete=django.db.models.deletion.SET_NULL, to='okmessages.Message', null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(related_name='sent_messages', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
