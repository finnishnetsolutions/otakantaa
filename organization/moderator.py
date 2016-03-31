# coding=utf-8

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from libs.moderation import moderation
from organization.models import AdminSettings
from otakantaa.moderator import BaseModerator

from .models import Organization
from otakantaa.utils import send_email_to_multiple_receivers


class OrganizationModerator(BaseModerator):
    auto_approve_unless_flagged = False
    visibility_column = 'is_active'

    def approve_object(self, moderated_object, moderator=None):
        moderated_object.content_object.is_active = True
        moderated_object.content_object.activated = timezone.now()
        moderated_object.content_object.save()

        unapproved_admins = AdminSettings.objects.filter(
            organization=moderated_object.content_object, approved=False)

        for a in unapproved_admins.all():
            a.approved = True
            a.save()

        receivers = [u for u in moderated_object.content_object.admins.all()]
        send_email_to_multiple_receivers(
            _("Organisaatio on aktivoitu"),
            'organization/email/organization_activated.txt',
            {'organization': moderated_object.content_object},
            receivers,
        )


class AdminSettingsModerator(BaseModerator):
    auto_approve_unless_flagged = True
    moderation_queue_template_name = 'organization/organization_admins_moderation.html'
    visibility_column = 'approved'

    def get_object_url(self, obj):
        return obj.organization.get_absolute_url()

    def approve_object(self, moderated_object, moderator=None):
        super(AdminSettingsModerator, self).approve_object(moderated_object, moderator)

        send_email_to_multiple_receivers(
            _("Hyväksyntä organisaation yhteyshenkilöksi"),
            'organization/email/organization_admin_approved.txt',
            {'organization': moderated_object.content_object.organization},
            [moderated_object.content_object.user],
        )


moderation.register(Organization, OrganizationModerator)
moderation.register(AdminSettings, AdminSettingsModerator)
