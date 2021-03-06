# coding=utf-8

from __future__ import unicode_literals

from django import template


register = template.Library()


@register.assignment_tag
def permitted(perm_check_obj, **kwargs):
    return perm_check_obj.check(**kwargs)
