# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from libs.permitter import perms

from otakantaa import perms as otakantaa

from .models import User


class OwnAccount(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.account = kwargs.pop('obj')
        super(OwnAccount, self).__init__(**kwargs)

    def is_authorized(self):
        return self.user.pk == self.account.pk


class UserEmailSpecified(otakantaa.BasePermission):
    def get_login_url(self):
        return reverse('account:settings', kwargs={'user_id': self.request.user.pk})

    def get_unauthorized_message(self):
        return ugettext("Sinun on määriteltävä sähköpostiosoitteesi ennen jatkamista.")

    def is_authorized(self):
        return bool(self.user.settings.email)


class IsClosed(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.account = kwargs.pop("obj")
        super(IsClosed, self).__init__(**kwargs)

    def get_unauthorized_message(self):
        return ugettext("Käyttäjätiliä ei ole.")

    def get_login_url(self):
        return reverse('schemes')

    def is_authorized(self):
        return self.account.status == User.STATUS_ARCHIVED


CanEditUser = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(
        OwnAccount,
        otakantaa.IsAdmin,
        perms.And(
            otakantaa.IsModerator,
            otakantaa.ObjectIsParticipant
        )
    )
)

CanViewUserProfile = perms.Or(
    perms.And(
        perms.Not(IsClosed),
        OwnAccount,
    ),
    otakantaa.IsModerator
)
