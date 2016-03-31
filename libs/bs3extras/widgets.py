# coding=utf-8

from __future__ import unicode_literals

import json
from uuid import uuid4

from django import forms
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from bootstrap3_datetime import widgets as bs3_widgets


class LocalizedDateTimePicker(bs3_widgets.DateTimePicker):
    is_localized = True

    def __init__(self, *args, **kwargs):
        super(LocalizedDateTimePicker, self).__init__(*args, **kwargs)
        self.options["locale"] = self.options.pop("language")

    def render(self, name, value, attrs=None):
        """Copy-pasted from super to lazy-add language to the options json."""

        if value is None:
            value = ''
        input_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            input_attrs['value'] = force_text(self._format_value(value))
        input_attrs = dict([(key, conditional_escape(val))
                            for key, val in input_attrs.items()])  # python2.6 compatible
        if not self.picker_id:
            self.picker_id = input_attrs.get('id', '') + '_picker'
        self.div_attrs['id'] = self.picker_id
        picker_id = conditional_escape(self.picker_id)
        div_attrs = dict(
            [(key, conditional_escape(val))
             for key, val in self.div_attrs.items()])  # python2.6 compatible
        icon_attrs = dict([(key, conditional_escape(val))
                           for key, val in self.icon_attrs.items()])
        html = self.html_template % dict(div_attrs=flatatt(div_attrs),
                                         input_attrs=flatatt(input_attrs),
                                         icon_attrs=flatatt(icon_attrs))
        if not self.options:
            js = ''
        else:
            options = self.options.copy()
            options.setdefault("locale", get_language())
            options['format'] = self.conv_datetime_format_py2js(self.format)
            js = self.js_template % dict(picker_id=picker_id,
                                         options=json.dumps(options or {}))
        return mark_safe(force_text(html + js))


class InlineLocalizedDateTimePicker(LocalizedDateTimePicker):
    html_template = "<input%(input_attrs)s/>"

    def __init__(self, *args, **kwargs):
        super(InlineLocalizedDateTimePicker, self).__init__(*args, **kwargs)
        self.options["inline"] = True

    def render(self, name, value, attrs=None):
        inline_attrs = {"class": "hidden"}
        attrs = attrs.update(inline_attrs) if attrs else inline_attrs

        if value is None:
            value = ''
        input_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            input_attrs['value'] = force_text(self._format_value(value))
        input_attrs = dict([(key, conditional_escape(val))
                            for key, val in input_attrs.items()])  # python2.6 compatible

        html = self.html_template % dict(input_attrs=flatatt(input_attrs))
        if not self.options:
            js = ''
        else:
            options = self.options.copy()
            options.setdefault("locale", get_language())
            options['format'] = self.conv_datetime_format_py2js(self.format)
            js = self.js_template % dict(picker_id=input_attrs["id"],
                                         options=json.dumps(options or {}))
        return mark_safe(force_text(html + js))


class LocalizedTimePicker(LocalizedDateTimePicker):
    format_key = "TIME_INPUT_FORMATS"

    def __init__(self, options=None, icon_attrs=None, *args, **kwargs):
        if not icon_attrs:
            icon_attrs = {"class": "glyphicon glyphicon-time"}
        else:
            icon_attrs.setdefault("class", "glyphicon glyphicon-time")
        super(LocalizedTimePicker, self).__init__(options=options, icon_attrs=icon_attrs,
                                                  *args, **kwargs)


class BootstrapAddOnMixIn(object):
    addon_html_wrap = """
        <div class="input-group">
            <span class="input-group-addon">
                <span class="glyphicon glyphicon-{addon}"></span>
            </span>
            {input}
        </div>
    """
    addon = None

    def __init__(self, *args, **kwargs):
        self.addon = kwargs.pop('addon', self.addon)
        super(BootstrapAddOnMixIn, self).__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        html = super(BootstrapAddOnMixIn, self).render(*args, **kwargs)
        if self.addon is not None:
            html = mark_safe(self.addon_html_wrap.format(addon=self.addon, input=html))
        return html


class TokenInputSelectMixIn(object):
    json_encoder = json.JSONEncoder

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('tokeninput_options', {})
        super(TokenInputSelectMixIn, self).__init__(*args, **kwargs)

    def get_options(self):
        return self.options.copy()

    def render(self, name, value, attrs=None, choices=()):
        # Unique class name to avoid conflicts when duplicate input ids exist on the page.
        runtime_uid = 'tinput_{}_{}'.format(attrs['id'], uuid4().hex[:10])
        attrs.setdefault('class', '')
        attrs['class'] += ' {}'.format(runtime_uid)
        output = super(TokenInputSelectMixIn, self).render(name, value, attrs=attrs,
                                                           choices=choices)
        output = '{input}<script>$(".{runtime_uid}")' \
                 '.tokenInputizeSelect({opts});</script>'\
            .format(
                input=output, runtime_uid=runtime_uid,
                opts=json.dumps(self.get_options(), cls=self.json_encoder)
            )
        return mark_safe(output)


class TokenInputSelectWidget(BootstrapAddOnMixIn, TokenInputSelectMixIn, forms.Select):
    addon = 'search'


class TokenInputSelectMultipleWidget(BootstrapAddOnMixIn, TokenInputSelectMixIn,
                                     forms.SelectMultiple):
    addon = 'search'
