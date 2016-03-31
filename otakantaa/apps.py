# coding=utf-8

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from conversation.apps import ConversationAppConfig
from survey.apps import SurveyAppConfig


class OtakantaaSurveyAppConfig(SurveyAppConfig):
    SHOW_RESULTS_OWNERS = 3

    perms_path = "content.survey_perms"
    base_permission_class = "otakantaa.perms.BasePermission"
    show_results_choices = SurveyAppConfig.show_results_choices + (
        (SHOW_RESULTS_OWNERS, _("Omistajat")),
    )
    show_results_default = SurveyAppConfig.SHOW_RESULTS_EVERYONE
    client_identifier_path = "account.ClientIdentifier"
    get_client_identifier_path = "account.utils.get_client_identifier"


class OtakantaaConversationAppConfig(ConversationAppConfig):
    perms_path = "content.conversation_perms"
    base_permission_class = "otakantaa.perms.BasePermission"
