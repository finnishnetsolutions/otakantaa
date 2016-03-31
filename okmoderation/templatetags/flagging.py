# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext

from okmoderation.models import ContentFlag


register = template.Library()


@register.inclusion_tag('okmoderation/flag_content_link.html')
def flag_link(obj=None, label=None, extraclass=''):
    if label is None:
        label = ugettext("Ilmoita asiaton sisältö")
    return {
        'obj': obj,
        'ct': ContentType.objects.get_for_model(obj),
        'label': label,
        'extraclass': extraclass
    }


@register.assignment_tag
def flaggings(obj=None):
    return ContentFlag.objects.filter(content_type=ContentType.objects.get_for_model(obj),
                                      object_id=obj.pk,
                                      status=ContentFlag.STATUS_FLAGGED)
