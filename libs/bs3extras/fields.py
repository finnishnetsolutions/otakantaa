# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.utils.formats import get_format_lazy
from .widgets import LocalizedTimePicker

from .widgets import LocalizedDateTimePicker


class LocalizedDateTimeField(forms.DateTimeField):
    widget = LocalizedDateTimePicker

    def __init__(self, *args, **kwargs):
        self.format = get_format_lazy(kwargs.pop('format', 'DATETIMEPICKER_FORMAT'))
        kwargs.update({'localize': True,
                       'input_formats': get_format_lazy('DATETIME_INPUT_FORMATS',)})
        super(LocalizedDateTimeField, self).__init__(*args, **kwargs)
        self.widget.format = self.format


class LocalizedDateField(forms.DateField):
    widget = LocalizedDateTimePicker

    def __init__(self, *args, **kwargs):
        self.format = get_format_lazy(kwargs.pop('format', 'DATEPICKER_FORMAT'))
        kwargs.update({'localize': True,
                       'input_formats': get_format_lazy('DATE_INPUT_FORMATS',)})
        super(LocalizedDateField, self).__init__(*args, **kwargs)
        self.widget.format = self.format
        # type date collides with google chrome native picker
        # self.widget.input_type = 'date'


class LocalizedTimeField(forms.TimeField):
    widget = LocalizedTimePicker

    def __init__(self, seconds=True, *args, **kwargs):
        self.format = get_format_lazy(kwargs.pop("format", "TIMEPICKER_FORMAT"))
        kwargs.update({"localize": True,
                       "input_formats": get_format_lazy("TIME_INPUT_FORMATS",)})
        super(LocalizedTimeField, self).__init__(*args, **kwargs)
        self.widget.format = self.format