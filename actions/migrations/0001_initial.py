# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import actions.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=16, choices=[('created', 'created'), ('updated', 'updated'), ('deleted', 'deleted')])),
                ('subtype', models.CharField(default='', max_length=100)),
                ('object_id', models.PositiveIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            bases=(models.Model, actions.models.ActionTypeMixin),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=50)),
                ('send_instantly', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(related_name='notifications', to='actions.Action')),
                ('recipient', models.ForeignKey(related_name='notifications', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-id',),
                'get_latest_by': 'action__created',
            },
        ),
        migrations.CreateModel(
            name='SentEmails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=254)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('notification', models.ForeignKey(related_name='sent_emails', to='actions.Notification', null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='notification',
            unique_together=set([('action', 'recipient', 'role')]),
        ),
    ]
