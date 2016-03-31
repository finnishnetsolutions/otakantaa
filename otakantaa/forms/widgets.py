# coding=utf-8

from __future__ import unicode_literals

import json

from django import forms
from django.forms.widgets import SelectMultiple, Select
from django.utils.html import format_html, escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from libs.attachtor.forms.widgets import RedactorAttachtorWidget
from libs.multilingo.forms import widgets as multilingo
from otakantaa.utils import strip_tags


class Select2Multiple(SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        output = super(Select2Multiple, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").select2();</script>' % attrs['id'])


class Select2(Select):
    def render(self, name, value, attrs=None, choices=()):
        output = super(Select2, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").select2();</script>' % attrs['id'])


class ButtonSelectMixIn(object):
    def render(self, name, value, attrs=None, choices=()):
        if attrs is not None:
            opts = attrs.pop('buttonselect', {})
        else:
            opts = {}
        output = super(ButtonSelectMixIn, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").buttonSelect(%s);</script>' %
                         (attrs['id'], json.dumps(opts)))


class ButtonSelect(ButtonSelectMixIn, forms.Select):
    pass


class AutoSubmitButtonSelect(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        opts = attrs.copy() if attrs is not None else {}
        opts['changeEvent'] = 'change'
        output = super(AutoSubmitButtonSelect, self).render(name, value, attrs, choices)
        return mark_safe(output + """
            <script>
                $("#%s").buttonSelect(%s).on('change', function() {
                    $(this).parents('form').first().submit();
                });
            </script>
            """ % (attrs['id'], json.dumps(opts)))


class HtmlButtonSelectMixin(object):
    """ Allows html in choices label. """
    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html('<option value="{0}"{1} data-html="{2}">{3}</option>',
                           option_value,
                           selected_html,
                           escape(option_label),
                           strip_tags(option_label))


class HtmlButtonSelect(HtmlButtonSelectMixin, ButtonSelect):
    pass


class AutoSubmitHtmlButtonSelect(HtmlButtonSelectMixin, AutoSubmitButtonSelect):
    pass


class SingleLanguageRedactorAttachtorWidget(multilingo.SingleLanguageWidgetMixIn,
                                            RedactorAttachtorWidget):
    pass


class MultiLingualWidget(multilingo.MultiLingualWidget):
    def get_options(self):
        opts = super(MultiLingualWidget, self).get_options()
        opts.update({
            'langChoiceText': ugettext("Kieliversiot")
        })
        return opts


class MultiLingualWidgetWithTranslatedNotification(MultiLingualWidget):

    def render(self, name, value, attrs=None):
        html = super(MultiLingualWidgetWithTranslatedNotification, self).render(
            name, value, attrs)

        fully_translated = True
        for i, widget in enumerate(self.widgets):
            widget_value = None
            if isinstance(value, dict):
                widget_value = value.get(self._lang_code(i), None)
            elif isinstance(value, list) and len(value) > i:
                widget_value = value[i]
            if not widget_value:
                fully_translated = False

        if fully_translated:
            html += '<span class="fully-translated">({})</span>'.format(
                ugettext("Käännetty"))
        return html
