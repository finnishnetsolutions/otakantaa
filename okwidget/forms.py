# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from account.models import UserSettings
from content.forms import SchemeSearchForm


class WidgetForm(forms.Form):
    DEFAULT_LIMIT = 5
    LIMIT_CHOICES = [(k, k) for k in (3, 4, 5, 6, 7, 8, 9, 10)]
    limit = forms.ChoiceField(label=_("Näytettäviä tuloksia"), choices=LIMIT_CHOICES,
                              required=False, initial=DEFAULT_LIMIT)

    def __init__(self, data=None, *args, **kwargs):
        # Set default limit, if not given.
        if data is not None:
            data = data.copy()
            limit = data.get("limit")
            if limit is None:
                data["limit"] = self.DEFAULT_LIMIT
        super(WidgetForm, self).__init__(data, *args, **kwargs)

    def filtrate(self, qs):
        limit = self.cleaned_data.get("limit") or self.DEFAULT_LIMIT
        return qs[:limit]


class SchemeListWidgetForm(WidgetForm, SchemeSearchForm):
    DEFAULT_LANGUAGE = "fi"
    language = forms.ChoiceField(label=_("Kieli"), choices=UserSettings.LANGUAGE_CHOICES,
                                 required=False, initial=DEFAULT_LANGUAGE)

    def __init__(self, data=None, default_language=None, *args, **kwargs):
        # Set default language, if not given.
        if data is not None:
            data = data.copy()
            language = data.get("language")
            if language is None:
                data["language"] = default_language
        super(SchemeListWidgetForm, self).__init__(data, *args, **kwargs)

    def filtrate(self, qs):
        return WidgetForm.filtrate(self, (SchemeSearchForm.filtrate(self, qs)))

    def get_language(self):
        return self.cleaned_data.get("language", self.DEFAULT_LANGUAGE)
