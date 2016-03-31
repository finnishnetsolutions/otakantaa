# coding=utf-8

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from otakantaa.utils import get_site_name


def otakantaa_settings(req):
    return {
        'BASE_URL': settings.BASE_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        'PIWIK_ID': getattr(settings, 'PIWIK_ID', None),
        'PIWIK_URL': getattr(settings, 'PIWIK_URL', None),
        'PRACTICE': settings.PRACTICE,
        'SITE_NAME': get_site_name(),
        'ABSOLUTE_URI': "{}{}".format(settings.BASE_URL, req.path),
    }
