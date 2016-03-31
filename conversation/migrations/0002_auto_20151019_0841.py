# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('conversation', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('created',)},
        ),
        migrations.AddField(
            model_name='comment',
            name='comment',
            field=models.TextField(default='', max_length=3000, verbose_name='kommentti'),
        ),
        migrations.AddField(
            model_name='comment',
            name='conversation',
            field=models.ForeignKey(related_name='comments', to='conversation.Conversation', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='comment',
            name='ip_address',
            field=models.GenericIPAddressField(null=True, unpack_ipv4=True, blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='is_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='comment',
            name='quote',
            field=models.ManyToManyField(related_name='quoted', to='conversation.Comment'),
        ),
        migrations.AddField(
            model_name='comment',
            name='target_comment',
            field=models.ForeignKey(related_name='responses', blank=True, to='conversation.Comment', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='title',
            field=models.CharField(max_length=255, verbose_name='otsikko', blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='comments', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='user_name',
            field=models.CharField(max_length=50, verbose_name='nimimerkki', blank=True),
        ),
    ]
