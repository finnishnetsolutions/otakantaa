# coding=utf-8

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from libs.permitter import perms

from otakantaa import perms as otakantaa
from survey import default_perms
from survey.conf import config as survey_config
from survey.models import Survey

from .models import ParticipationDetails
from .perms import CanParticipateParticipation


class BaseSurveyPermissionExtended(default_perms.BaseSurveyPermission):
    def __init__(self, **kwargs):
        super(BaseSurveyPermissionExtended, self).__init__(**kwargs)
        self.participation_details = ParticipationDetails.objects.get(
            object_id=self.survey.pk,
            content_type=ContentType.objects.get_for_model(Survey)
        )

    def is_authorized(self):
        raise NotImplementedError()


class SurveyShowResultsOwners(default_perms.BaseSurveyPermission):
    def is_authorized(self):
        return self.survey.show_results == survey_config.SHOW_RESULTS_OWNERS


class OwnsSurvey(BaseSurveyPermissionExtended):
    def is_authorized(self):
        return self.user.pk in self.participation_details.scheme.owner_ids


class SurveyIsOpen(BaseSurveyPermissionExtended):
    def is_authorized(self):
        if self.participation_details.is_open():
            return CanParticipateParticipation(
                request=self.request, obj=self.participation_details).is_authorized()
        return False


class SurveyInteractionEveryone(BaseSurveyPermissionExtended):
    def is_authorized(self):
        scheme = self.participation_details.scheme
        return scheme.interaction == scheme.INTERACTION_EVERYONE


CanEditSurvey = perms.And(

    # removed condition so owners can write translations even after the survey has been
    # answered
    # default_perms.CanEditSurvey,
    perms.Or(OwnsSurvey, otakantaa.IsModerator),
)

CanAnswerSurvey = perms.And(
    default_perms.CanAnswerSurvey,
    SurveyIsOpen,
    perms.Not(OwnsSurvey),
    perms.Or(
        otakantaa.IsAuthenticated,
        SurveyInteractionEveryone
    )
)

ShowSurveyResults = perms.Or(
    OwnsSurvey,
    default_perms.ShowSurveyResults,
    perms.And(SurveyShowResultsOwners, OwnsSurvey),
)
