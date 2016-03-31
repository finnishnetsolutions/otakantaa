# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Municipality',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=3)),
                ('oid', models.CharField(max_length=32, unique=True, null=True, blank=True)),
                ('name_fi', models.CharField(max_length=50, db_index=True)),
                ('name_sv', models.CharField(max_length=50, db_index=True)),
                ('beginning_date', models.DateField()),
                ('expiring_date', models.DateField()),
                ('created_date', models.DateField()),
                ('last_modified_date', models.DateField()),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Municipalities',
            },
        ),
        migrations.CreateModel(
            name='Restructuring',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('old_code', models.CharField(max_length=3)),
                ('new_code', models.CharField(max_length=3)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('new_municipality', models.ForeignKey(related_name='old_municipalities', verbose_name='Former municipalities', to='fimunicipality.Municipality')),
                ('old_municipality', models.ForeignKey(related_name='new_municipalities', verbose_name='New municipalities', to='fimunicipality.Municipality')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='municipality',
            index_together=set([('beginning_date', 'expiring_date')]),
        ),
        migrations.AlterUniqueTogether(
            name='restructuring',
            unique_together=set([('old_municipality', 'new_municipality')]),
        ),
    ]
