
# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from libs.fimunicipality.models import Municipality

from otakantaa.forms.widgets import Select2Multiple
from otakantaa.forms.fields import ModelMultipleChoiceField
from organization.models import Organization
from tagging.models import Tag
from account.models import User
from .models import Favorite


class FavoriteTagForm(forms.ModelForm):

    favorites = ModelMultipleChoiceField(label='', widget=Select2Multiple,
                                         queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        type = kwargs.pop('type')
        queryset = self.get_queryset(type)
        kwargs['initial'] = {'favorites': self.get_favorites(
            kwargs['instance'], queryset.model
        ).values_list('object_id', flat=True)}

        super(FavoriteTagForm, self).__init__(*args, **kwargs)
        self.fields['favorites'].queryset = queryset

    def get_favorites(self, instance, model):
        ct = ContentType.objects.get_for_model(model)
        return instance.favorites.filter(content_type=ct)

    @transaction.atomic()
    def save(self):
        self.get_favorites(
            self.instance,
            self.fields['favorites'].queryset.model
        ).delete()

        for item in self.cleaned_data['favorites']:
            Favorite(content_object=item, user=self.instance).save()

    def get_queryset(self, type):
        if type == Favorite.TYPE_TAG:
            return Tag.objects.all()
        elif type == Favorite.TYPE_ORGANIZATION:
            return Organization.objects.normal()
        elif type == Favorite.TYPE_MUNICIPALITY:
            return Municipality.objects.natural().active()
        return None

    class Meta:
        model = User
        fields = ('favorites', )



