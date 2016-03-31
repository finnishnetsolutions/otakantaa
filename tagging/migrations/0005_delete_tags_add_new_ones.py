# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models, migrations


def add_tags(apps, schema_editor):
    tags = [
        "asuminen ja rakentaminen",
        "ympäristö ja luonto",
        "työelämä",
        "talous",
        "sosiaali- ja terveyspalvelut",
        "liikenne",
        "tietoyhteiskunta ja viestintä",
        "turvallisuus",
        "tiede ja tutkimus",
        "opetus ja koulutus",
        "kulttuuri ja vapaa-aika",
        "hallinto ja kehittäminen",
        "lainsäädäntö ja oikeudet",
        "Muut"
    ]

    # Delete all tags and add the new ones.
    Tag = apps.get_model("tagging", "Tag")
    Tag.objects.all().delete()
    for tag in tags:
        Tag.objects.create(name=tag)


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0004_auto_20151116_1052'),
    ]

    operations = [
        migrations.RunPython(add_tags)
    ]
