# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models, migrations


def add_tags(apps, schema_editor):
    tags = [
        "Asuminen",
        "Rakentaminen",
        "Luonto",
        "Ympäristö",
        "Koulu",
        "Opiskelu",
        "Kulttuuri",
        "Työelämä",
        "Vapaa-aika",
        "Harrastukset",
        "Tapahtumat",
        "Matkailu",
        "Liikenne",
        "Palvelut",
        "Terveys",
        "Muut"
    ]

    # Delete all tags and add the new ones.
    Tag = apps.get_model("tagging", "Tag")
    Tag.objects.all().delete()
    for tag in tags:
        Tag.objects.create(name=tag)


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_tags)
    ]
