# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def copy_owners(apps, schema_editor):
    Scheme = apps.get_model('content', 'Scheme')
    SchemeOwners = apps.get_model('content', 'SchemeOwner')
    for s in Scheme.objects.all():
        for o in s.temp_owners.all():
            SchemeOwners.objects.create(user=o, scheme=s)


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0003_organization_activated'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0011_auto_20151123_1434'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchemeOwner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('organization', models.ForeignKey(related_name='schemes', to='organization.Organization', null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='scheme',
            name='owners',
        ),
        migrations.AddField(
            model_name='schemeowner',
            name='scheme',
            field=models.ForeignKey(related_name='owners', to='content.Scheme'),
        ),
        migrations.AddField(
            model_name='schemeowner',
            name='user',
            field=models.ForeignKey(related_name='schemes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(copy_owners),
    ]
