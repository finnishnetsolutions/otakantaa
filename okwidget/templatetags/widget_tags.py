# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def widget_modal_url(context):
    base_url = reverse("widget:modal")
    if len(context.request.GET):
        return "{}?{}".format(base_url, context.request.GET.urlencode())
    return base_url


@register.simple_tag(takes_context=True)
def widget_content_url(context):
    base_url = reverse("widget:widget")
    if len(context.request.GET):
        return "{}?{}".format(base_url, context.request.GET.urlencode())
    return base_url
