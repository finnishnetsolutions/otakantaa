# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import content.models
import otakantaa.models
import django.db.models.deletion
from django.conf import settings
import imagekit.models.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('fimunicipality', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tagging', '0002_delete_tags_add_new_ones'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('picture_alt_text', models.CharField(default=None, max_length=255, null=True, verbose_name='kuvan tekstimuotoinen kuvaus (suositeltava)')),
                ('title', otakantaa.models.MultilingualTextField(default='', help_text=None, max_length=255, verbose_name='otsikko')),
                ('description', otakantaa.models.MultilingualRedactorField(default='', help_text=None, verbose_name='sis\xe4lt\xf6', blank=True)),
                ('status', models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Avoin'), (6, 'P\xe4\xe4ttynyt')])),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('published', models.DateTimeField(default=None, null=True, blank=True)),
                ('visibility', models.SmallIntegerField(default=1, verbose_name='n\xe4kyvyys', choices=[(1, 'Luonnos'), (10, 'Julkinen'), (8, 'Arkistoitu')])),
                ('interaction', models.SmallIntegerField(default=1, verbose_name='Kuka saa ottaa kantaa, vastata kyselyyn ja ottaa osaa keskusteluun?', choices=[(1, 'Kaikki'), (2, 'Rekister\xf6ityneet k\xe4ytt\xe4j\xe4t')])),
                ('picture', imagekit.models.fields.ProcessedImageField(upload_to=content.models._scheme_main_pic_path)),
                ('archived', models.DateTimeField(default=None, null=True, blank=True)),
                ('creator', models.ForeignKey(related_name='creator', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('modifier', models.ForeignKey(related_name='modifier', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('owner_organizations', models.ManyToManyField(related_name='schemes', verbose_name='omistajaorganisaatiot', to='organization.Organization')),
                ('owners', models.ManyToManyField(related_name='schemes', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(to='tagging.Tag', verbose_name='teemat')),
                ('target_municipalities', models.ManyToManyField(related_name='targeted_schemes', verbose_name='kohdekunnat', to='fimunicipality.Municipality')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
