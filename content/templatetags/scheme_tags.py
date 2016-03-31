# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.core.urlresolvers import reverse

register = template.Library()

# @todo: not in use. Where is only the first organization necessary?
@register.assignment_tag
def scheme_owner_organization(scheme):
    owner = scheme.owners \
        .select_related("organization") \
        .filter(organization_id__isnull=False) \
        .first()
    if owner:
        return owner.organization


@register.simple_tag(takes_context=True)
def load_schemes_url(context, page_obj):
    url = reverse("content:load_schemes")
    if page_obj.has_next():
        page = page_obj.next_page_number()

    data = context["request"].GET.copy()
    if data.get("page"):
        del data["page"]

    if data:
        url = "{}?{}&page={}".format(url, data.urlencode(), page)
    else:
        url = "{}?page={}".format(url, page)

    return url
