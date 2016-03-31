# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from otakantaa.utils import strip_tags


def update_search_text(apps, schema_editor):
    Scheme = apps.get_model('content', 'Scheme')
    schemes = Scheme.objects.all()

    for s in schemes:
        s.search_text = ' '.join(map(strip_tags,
                                     s.description.values()
                                     + s.title.values()
                                     + s.lead_text.values()
                                     ))
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0024_scheme_search_text'),
    ]

    operations = [
        migrations.RunPython(update_search_text)
    ]
