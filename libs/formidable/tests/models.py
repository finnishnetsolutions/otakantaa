# coding=utf-8

from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Contact(models.Model):
    name = models.CharField(max_length=100)


class ContactPhone(models.Model):
    TYPE_MOBILE = 1
    TYPE_LANDLINE = 2
    TYPE_CHOICES = (
        (TYPE_MOBILE, _("Mobile")),
        (TYPE_LANDLINE, _("Landline")),
    )

    contact = models.ForeignKey(Contact, related_name='phones')
    number = models.CharField(max_length=25)
    type = models.IntegerField(choices=TYPE_CHOICES)
    when_to_call = models.CharField(max_length=25, blank=True)
    update_lock = models.BooleanField(default=False)
    delete_lock = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)


class User(models.Model):
    username = models.CharField(max_length=25)


class Profile(models.Model):
    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    dob = models.DateField()
    updated = models.DateTimeField(auto_now=True)
    update_lock = models.BooleanField(default=False)
