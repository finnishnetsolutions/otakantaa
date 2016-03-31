# coding=utf-8

from __future__ import unicode_literals

from django.apps.config import AppConfig
from django.utils.translation import ugettext_lazy as _


class ConversationAppConfig(AppConfig):
    name = 'conversation'

    perms_path = 'conversation.default_perms'
    base_permission_class = 'libs.permitter.perms.FriendlyRequestPermission'

