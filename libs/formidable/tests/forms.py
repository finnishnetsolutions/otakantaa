# coding=utf-8

from __future__ import unicode_literals

from datetime import date

from django import forms

from ..forms.forms import FormidableForm, FormidableModelForm
from ..forms.fields import InlineFormSetField, InlineFormField
from ..forms.widgets import BootstrapInlineFormWidget, BootstrapInlineFormSetWidget

from .models import Contact, ContactPhone, User, Profile


class BasicPhoneForm(forms.Form):
    number = forms.CharField(max_length=25)
    type = forms.ChoiceField(choices=ContactPhone.TYPE_CHOICES)


class BasicContactForm(FormidableForm):
    name = forms.CharField(max_length=50)
    phones = InlineFormSetField(BasicPhoneForm, initial_forms=1)


class PhoneModelForm(forms.ModelForm):
    class Meta:
        model = ContactPhone
        fields = ('number', 'type', )


class ContactModelForm(FormidableModelForm):
    phones = InlineFormSetField(
        PhoneModelForm,
        related_name='contact',
        min_forms=1,
        max_forms=4,
        initial_forms=1,
        can_delete=lambda obj: obj is None or obj.delete_lock is False,
        can_update=lambda obj: obj is None or obj.update_lock is False,
        widget=BootstrapInlineFormSetWidget
    )

    class Meta:
        fields = ('name', 'phones', )
        model = Contact


class BasicProfileForm(forms.Form):
    first_name = forms.CharField(max_length=25)
    last_name = forms.CharField(max_length=25)
    dob = forms.DateField()


class BasicUserForm(FormidableForm):
    username = forms.CharField(max_length=25)
    profile = InlineFormField(BasicProfileForm)


class ProfileModelForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'dob', )


class UserModelForm(FormidableModelForm):
    profile = InlineFormField(
        ProfileModelForm,
        related_name='user',
        can_update=lambda obj: obj is None or obj.update_lock is False,
        can_create=lambda obj: obj.dob > date(1900, 1, 1),
        widget=BootstrapInlineFormWidget
    )

    class Meta:
        model = User
        fields = ('username', 'profile', )


class UserModelFormWithBasicProfileForm(FormidableModelForm):
    basic_profile = InlineFormField(BasicProfileForm)

    class Meta:
        model = User
        fields = ('username', 'basic_profile', )
