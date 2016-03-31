# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import imagekit.models.fields
import django.core.validators
import account.models


class Migration(migrations.Migration):

    dependencies = [
        ('fimunicipality', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(help_text='Enint\xe4\xe4n 30 merkki\xe4. Vain kirjaimet, numerot ja _ ovat sallittuja.', unique=True, max_length=30, verbose_name='k\xe4ytt\xe4j\xe4nimi', validators=[django.core.validators.RegexValidator('^[\\w]+$', 'Enter a valid username.', 'invalid')])),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('status', models.SmallIntegerField(default=0, verbose_name='tila', choices=[(0, 'Odottaa aktivointia'), (1, 'Aktiivinen'), (5, 'Arkistoitu')])),
                ('joined', models.DateTimeField(auto_now_add=True, verbose_name='liittynyt')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='muokattu')),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('organizations', models.ManyToManyField(related_name='admins', to='organization.Organization')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'K\xe4ytt\xe4j\xe4',
                'verbose_name_plural': 'K\xe4ytt\xe4j\xe4t',
            },
        ),
        migrations.CreateModel(
            name='ClientIdentifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('hash', models.CharField(unique=True, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=50, verbose_name='etunimi')),
                ('last_name', models.CharField(max_length=50, verbose_name='sukunimi')),
                ('language', models.CharField(default='fi', max_length=5, verbose_name='kieli', choices=[('fi', 'suomi'), ('sv', 'ruotsi')])),
                ('email', models.EmailField(unique=True, max_length=254, verbose_name='s\xe4hk\xf6posti', blank=True)),
                ('picture', imagekit.models.fields.ProcessedImageField(upload_to=account.models._user_profile_pic_path)),
                ('municipality', models.ForeignKey(to='fimunicipality.Municipality')),
                ('user', models.OneToOneField(related_name='settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'K\xe4ytt\xe4j\xe4asetus',
                'verbose_name_plural': 'K\xe4ytt\xe4j\xe4asetukset',
            },
        ),
    ]
