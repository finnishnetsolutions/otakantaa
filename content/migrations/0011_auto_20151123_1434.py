# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def copy_owners(apps, schema_editor):
    Scheme = apps.get_model('content', 'Scheme')
    for s in Scheme.objects.all():
        for o in s.owners.all():
            s.temp_owners.add(o)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0010_auto_20151116_1052'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheme',
            name='owner_organizations',
        ),
        migrations.AddField(
            model_name='scheme',
            name='temp_owners',
            field=models.ManyToManyField(related_name='temp_owners', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='scheme',
            name='owners',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(copy_owners),
    ]
