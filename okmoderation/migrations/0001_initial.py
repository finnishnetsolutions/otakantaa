# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0004_user_schemes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('reason', models.CharField(help_text='Kerro lyhyesti, mik\xe4 tekee sis\xe4ll\xf6st\xe4 asiattoman. Enint\xe4\xe4n 250 merkki\xe4.', max_length=250, verbose_name='syy ilmoitukseen')),
                ('status', models.SmallIntegerField(default=1, verbose_name='tila', choices=[(1, 'ilmoitettu'), (2, 'ilmoitus hyl\xe4tty'), (3, 'ilmoitus hyv\xe4ksytty')])),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('client_identifier', models.ForeignKey(related_name='flagged_content', to='account.ClientIdentifier')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('flagger', models.ForeignKey(related_name='flagged_content', verbose_name='ilmoittaja', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ModerationReason',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('reason', models.CharField(max_length=250)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('moderator', models.ForeignKey(related_name='moderated_content', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterIndexTogether(
            name='moderationreason',
            index_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentflag',
            unique_together=set([('flagger', 'content_type', 'object_id'), ('client_identifier', 'content_type', 'object_id')]),
        ),
    ]
