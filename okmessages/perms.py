# coding=utf-8

from __future__ import unicode_literals

from libs.permitter import perms

from otakantaa import perms as otakantaa


class ReceiverIsSelf(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.target_user = kwargs["obj"]
        super(ReceiverIsSelf, self).__init__(**kwargs)

    def is_authorized(self):
        return self.user == self.target_user


class ReceiverIsModerator(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.target_user = kwargs["obj"]
        super(ReceiverIsModerator, self).__init__(**kwargs)

    def is_authorized(self):
        return self.target_user.is_moderator


class ReceiverIsOrganizationAdmin(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.target_user = kwargs["obj"]
        super(ReceiverIsOrganizationAdmin, self).__init__(**kwargs)

    def is_authorized(self):
        result = self.target_user.organizations.all().exists()
        return result


CanSendMessageTo = perms.And(
    otakantaa.IsAuthenticated,
    perms.Not(ReceiverIsSelf),
    perms.Or(
        otakantaa.IsModerator,
        perms.Or(
            ReceiverIsModerator,
            ReceiverIsOrganizationAdmin
        )
    )
)