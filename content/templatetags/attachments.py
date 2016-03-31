# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.core.urlresolvers import reverse

from content.models import Scheme, ParticipationDetails
from content.perms import CanEditScheme, CanEditParticipation

register = template.Library()


@register.filter()
def get_class_name(obj):
    return obj.__class__.__name__


@register.simple_tag(takes_context=True)
def get_attachments_edit_url(context, obj, asvar):
    if obj.__class__ == Scheme and CanEditScheme(request=context['request'], obj=obj).\
            is_authorized():
        context[asvar] = reverse('content:add_attachments', kwargs={'scheme_id': obj.pk})
    elif obj.__class__ == ParticipationDetails and \
            CanEditParticipation(request=context['request'], obj=obj).is_authorized():
        context[asvar] = reverse('content:participation:add_attachments', kwargs={
            'scheme_id': obj.scheme.pk, 'participation_detail_id': obj.pk})
    return ''


@register.simple_tag(takes_context=True)
def get_attachments_delete_url(context, obj, attachment, asvar):
    scheme = obj if obj.__class__ == Scheme else obj.scheme
    if CanEditScheme(request=context['request'], obj=scheme).is_authorized():
        context[asvar] = reverse('content:delete_attachment', kwargs={
            'scheme_id': scheme.pk, 'upload_id': attachment.pk})
    return ''
