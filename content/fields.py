# coding=utf-8

from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.utils.translation import ugettext_lazy as _
from django.utils import six
from multiupload.fields import MultiFileField

from otakantaa.forms.fields import SaferFileField, ModelMultipleChoiceField

from .widgets import SchemeAdminOwnersSelect2Multiple


class CustomMultiFileField(MultiFileField):
    default_error_messages = {
        'min_num': _("Liitettävien tiedostojen vähimmäismäärä on {min_num}"),
        'max_num': _("Liitettävien tiedostojen enimmäismäärä on {max_num}"),
        'file_size': _("Tiedosto {uploaded_file_name} ylittää kokorajoituksen "
                       "{maximum_file_size}"),
    }

    def validate(self, data):
        FileField().validate(data)

        num_files = 0 if len(data) and not data[0] else len(data)

        errors = []
        if num_files < self.min_num:
            errors.extend(ValidationError(
                self.error_messages['min_num'].format(min_num=self.min_num)))
        elif self.max_num and num_files > self.max_num:
            errors.extend(ValidationError(
                self.error_messages['max_num'].format(max_num=self.max_num)))
        for uploaded_file in data:
            SaferFileField().run_validators(uploaded_file)

            if self.maximum_file_size and uploaded_file.size > self.maximum_file_size:
                errors.extend(ValidationError(
                    self.error_messages['file_size'].format(
                        uploaded_file_name=uploaded_file.name,
                        maximum_file_size=self.maximum_file_size)))
        if errors:
            raise ValidationError(errors)


class SchemeAdminOwnersMultiChoiceField(ModelMultipleChoiceField):
    """
    Handles either User.organizations.through or a User queryset
    If not User queryset value will be formatted to user_id and organization_id
    separated by colon.
    """

    label_without_user = False
    user_qs = False
    widget = SchemeAdminOwnersSelect2Multiple

    def __init__(self, *args, **kwargs):
        if 'label_without_user' in kwargs:
            self.label_without_user = kwargs.pop('label_without_user')
        super(SchemeAdminOwnersMultiChoiceField, self).__init__(*args, **kwargs)

        if self.queryset.model.__name__ == 'User':
            self.user_qs = True

    def prepare_value(self, value):
        # value is a single object from queryset
        if hasattr(value, '_meta'):
            return self._format_value(value)
        # value is a list of objects
        elif hasattr(value, '__iter__') and len(value) and \
                not isinstance(value[0], six.text_type):
            return [self._format_value(v) for v in value]

        # value should be ok
        return super(SchemeAdminOwnersMultiChoiceField, self).prepare_value(value)

    def label_from_instance(self, obj):
        if self.label_without_user:
            return obj.organization
        elif self.user_qs:
            return obj
        return "{}: {}".format(obj.organization, obj.user)

    def _format_value(self, value):
        if self.user_qs:
            return value.pk
        return "{}:{}".format(value.user_id, value.organization_id)

    def clean(self, value):
        if isinstance(value, list) and len(value) and isinstance(value[0], six.text_type):
            value_list = []
            for val in value:
                if self.user_qs:
                    value_list.append(val)
                else:
                    u_pk, o_pk = val.split(":")
                    value_list.append(self.queryset.get(
                        user_id=u_pk, organization_id=o_pk).pk)
        else:
            value_list = value
        return super(SchemeAdminOwnersMultiChoiceField, self).clean(value_list)
