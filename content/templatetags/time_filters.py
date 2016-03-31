# coding=utf-8

from __future__ import unicode_literals
from datetime import date, datetime
from django.utils.translation import ugettext_lazy as _
from django import template

register = template.Library()


@register.filter(expects_localtime=True)
def days_until(value, arg=None):
    try:
        tzinfo = getattr(value, 'tzinfo', None)
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    today = datetime.now(tzinfo).date()
    delta = value - today

    if delta.days >= 1:
        return "%s %s" % (abs(delta.days), _("pv"))
    return ''
