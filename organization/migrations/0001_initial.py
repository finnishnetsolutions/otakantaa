# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import imagekit.models.fields
import otakantaa.models
import organization.models


class Migration(migrations.Migration):

    dependencies = [
        ('fimunicipality', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.SmallIntegerField(verbose_name='tyyppi', choices=[(1, 'Julkishallinto'), (2, 'J\xe4rjest\xf6'), (10, 'Muu organisaatio')])),
                ('name', otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='nimi')),
                ('description', otakantaa.models.MultilingualRedactorField(default='', help_text=None, verbose_name='kuvaus', blank=True)),
                ('picture', imagekit.models.fields.ProcessedImageField(default=None, null=True, upload_to=organization.models._organization_pic_path, blank=True)),
                ('is_active', models.BooleanField(default=False, verbose_name='aktiivinen')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, verbose_name='luotu')),
                ('search_text', models.TextField(default=None, null=True)),
                ('municipalities', models.ManyToManyField(related_name='Kunnat', verbose_name='Valitse kunnat, joiden alueella organisaatio toimii.', to='fimunicipality.Municipality')),
            ],
            options={
                'verbose_name': 'organisaatio',
                'verbose_name_plural': 'organisaatiot',
            },
        ),
    ]
