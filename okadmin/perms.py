# coding=utf-8

from __future__ import unicode_literals

from libs.permitter import perms
from otakantaa import perms as otakantaa
from account import perms as account


CanAccessAdminPanel = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(otakantaa.IsModerator, otakantaa.IsAdmin),
)

CanEditUser = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(
        perms.And(
            account.OwnAccount,
            otakantaa.IsModerator
        ),
        perms.And(
            otakantaa.IsModerator,
            otakantaa.ObjectIsParticipant
        ),
        otakantaa.IsAdmin
    )
)