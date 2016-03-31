# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def update_relations(apps, schema_editor):
    Organization = apps.get_model('organization', 'Organization')
    AdminSettings = apps.get_model('organization', 'AdminSettings')

    orgs = Organization.objects.filter(admins__isnull=False).distinct()

    for o in orgs:
        for u in o.admins.all():
            AdminSettings.objects.create(user=u, organization=o)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0005_organization_twitter_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(to='organization.Organization')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(update_relations)
    ]
