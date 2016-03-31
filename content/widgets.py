# coding=utf-8

from __future__ import unicode_literals

import re
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from otakantaa.forms.widgets import Select2Multiple


class SchemeAdminOwnersSelect2Multiple(Select2Multiple):
    """
    Scheme instance has to be set in form init
    self.fields['owners'].widget.instance = self.instance
    """

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        extra_class = ''
        selected_objects = self._transform_selected_values(selected_choices)
        if option_value in selected_objects:
            extra_class = ''
            if selected_objects[option_value] is not None and \
                    not selected_objects[option_value].approved:
                extra_class = mark_safe(' class="not-approved"')
            selected_html = mark_safe(' selected="selected"')
        else:
            selected_html = ''
        return format_html('<option value="{}"{}{}>{}</option>',
                           option_value,
                           selected_html,
                           extra_class,
                           force_text(option_label))

    def is_multi_value(self, value):
        return re.match(r'^\d+:\d+$', value)

    def _transform_selected_values(self, selected):
        transformed = {}
        for value in selected:
            if self.is_multi_value(value):
                u_pk, o_pk = value.split(":")
                options = {'user_id': u_pk, 'organization_id': o_pk}
                selected_key = value
            else:
                value = str(value)
                options = {'pk': value}
                selected_key = None

            transformed[selected_key] = None
            if hasattr(self, 'instance'):
                try:
                    obj = self.instance.owners.get(**options)
                    if not selected_key:
                        selected_key = str(obj.user_id)
                    transformed[selected_key] = obj
                except ObjectDoesNotExist:
                    # a new selection. value already set
                    pass
        return transformed
