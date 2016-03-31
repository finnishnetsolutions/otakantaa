# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.core.validators import EMPTY_VALUES
from django.forms.fields import FileField, Field
from django_bleach.forms import BleachField

from libs.attachtor.forms.fields import RedactorAttachtorFieldMixIn
from libs.attachtor.forms.widgets import RedactorAttachtorWidget
from libs.multilingo.forms.fields import SingleLanguageFieldMixIn, \
    MultiLingualField

from otakantaa.forms.validators import safe_extension_validator, antivirus_validator, \
    validate_multiple_emails
from otakantaa.forms.widgets import SingleLanguageRedactorAttachtorWidget

from .widgets import Select2Multiple


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = Select2Multiple

    def __init__(self, *args, **kwargs):
        """Remove Django's ugly help_text hack, until we have Django 1.8."""
        super(ModelMultipleChoiceField, self).__init__(*args, **kwargs)
        self.help_text = kwargs.get('help_text', None)


class SaferRedactorField(RedactorAttachtorFieldMixIn, BleachField):
    widget_class = RedactorAttachtorWidget

    def __init__(self, *args, **kwargs):
        options = kwargs.pop('redactor_options', {})
        allow_file_upload = kwargs.pop('allow_file_upload', True)
        allow_image_upload = kwargs.pop('allow_image_upload', True)
        super(SaferRedactorField, self).__init__(*args, **kwargs)
        self.widget = self.widget_class(
            redactor_options=options,
            allow_file_upload=allow_file_upload,
            allow_image_upload=allow_image_upload
        )


class SingleLanguageRedactorField(SingleLanguageFieldMixIn, SaferRedactorField):
    widget_class = SingleLanguageRedactorAttachtorWidget


class MultilingualRedactorField(RedactorAttachtorFieldMixIn, MultiLingualField):
    field_widget = SingleLanguageRedactorAttachtorWidget
    field_class = SingleLanguageRedactorField

    def _get_upload_group_id(self):
        return self._upload_group_id

    def _set_upload_group_id(self, val):
        self._upload_group_id = val
        for w in self.widget.widgets:
            w.upload_group_id = val

    upload_group_id = property(_get_upload_group_id, _set_upload_group_id)


class SaferFileField(FileField):
    default_validators = [safe_extension_validator, antivirus_validator, ]


class MultiEmailField(Field):
    default_validators = [validate_multiple_emails]

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop("token", " ")
        super(MultiEmailField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []
        value = [item.strip() for item in value.split(self.token) if item.strip()]
        return list(set(value))
