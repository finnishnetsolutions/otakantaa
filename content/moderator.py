# coding=utf-8

from __future__ import unicode_literals
from content.models import ParticipationDetails
from libs.moderation import moderation
from libs.moderation.managers import ModerationObjectsManager
from .models import Scheme
from otakantaa.moderator import BaseModerator


class SchemeManager(ModerationObjectsManager):
    def filter_moderated_objects(self, query_set):
        return query_set.filter(visibility=Scheme.VISIBILITY_PUBLIC)


class SchemeModerator(BaseModerator):
    moderation_queue_template_name = 'scheme/scheme_moderation.html'
    # moderation_manager_class = SchemeManager


class ParticipationModerator(BaseModerator):
    moderation_queue_template_name = 'participation/scheme_moderation.html'


moderation.register(Scheme, SchemeModerator)
moderation.register(ParticipationDetails, SchemeModerator)
