# coding=utf-8

from __future__ import unicode_literals

from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from conversation.models import Comment

from libs.permitter import perms

from .conf import config
from .models import Vote
from .utils import get_voter

BasePermission = import_string(config.base_permission_class)


class BaseConversationPermission(BasePermission):
    def __init__(self, **kwargs):
        self.conversation = kwargs['obj']
        # sometimes class needs to be initialized with comment object
        if hasattr(self.conversation, 'conversation') \
                and self.conversation.__class__ is Comment:
            self.conversation = self.conversation.conversation
        super(BaseConversationPermission, self).__init__(**kwargs)

    def is_authorized(self):
        raise NotImplementedError()


class BaseCommentPermission(BasePermission):
    def __init__(self, **kwargs):
        self.comment = kwargs['obj']
        super(BaseCommentPermission, self).__init__(**kwargs)

    def is_authorized(self):
        raise NotImplementedError()


