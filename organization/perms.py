# coding=utf-8

from __future__ import unicode_literals

from otakantaa import perms as otakantaa

from libs.permitter import perms


class OrganizationBasePermission(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.organization = kwargs['obj']
        super(OrganizationBasePermission, self).__init__(**kwargs)

    def is_authorized(self):
        return False


class IsOrganizationAdmin(OrganizationBasePermission):
    def is_authorized(self):
        return bool(self.organization.adminsettings_set.filter(
            user=self.user.pk, approved=True))


class OrganizationIsPublic(OrganizationBasePermission):
    def is_authorized(self):
        return self.organization.is_active is True


class OrganizationAwaitsModeratorActivation(OrganizationBasePermission):
    def is_authorized(self):
        return self.organization.awaits_activation()


CanViewOrganization = perms.Or(
    OrganizationIsPublic,
    perms.And(
        otakantaa.IsAuthenticated,
        perms.Or(IsOrganizationAdmin, otakantaa.IsModerator)
    )
)

CanEditOrganization = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(IsOrganizationAdmin, otakantaa.IsModerator)
)

CanActivateOrganization = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(
        perms.And(CanEditOrganization, perms.Not(OrganizationAwaitsModeratorActivation)),
        otakantaa.IsModerator,
    )
)

