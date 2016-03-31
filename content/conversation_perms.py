# coding=utf-8

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from content.perms import CanParticipateParticipation
from conversation.models import Conversation, Vote
from conversation.utils import get_voter

from libs.permitter import perms

from otakantaa import perms as otakantaa

from conversation import default_perms
from .models import ParticipationDetails


class BaseConversationPermissionExtended(default_perms.BaseConversationPermission):
    def __init__(self, **kwargs):
        super(BaseConversationPermissionExtended, self).__init__(**kwargs)

        if  hasattr(self.request, 'participation_detail'):
            self.participation_detail = self.request.participation_detail
        else:
            self.participation_detail = ParticipationDetails.objects.get(
                object_id=self.conversation.pk,
                content_type=ContentType.objects.get_for_model(Conversation)
            )

    def is_authorized(self):
        raise NotImplementedError()


class CommentIsVotedByUser(default_perms.BaseCommentPermission):
    unauthorized_message = _("Olet jo äänestänyt kommenttia.")

    def is_authorized(self):
        voter = get_voter(self.request, create=False)
        if voter:
            return Vote.objects.filter(
                voter=voter,
                comments=self.comment
            ).exists()
        else:
            return False


class OwnsConversation(BaseConversationPermissionExtended):
    def is_authorized(self):
        return self.user.pk in self.participation_detail.scheme.owner_ids


class ConversationIsOpen(BaseConversationPermissionExtended):
    def is_authorized(self):
        if self.participation_detail.is_open():
            return CanParticipateParticipation(
                request=self.request, obj=self.participation_detail).is_authorized()
        return False


class CommentCanBeVoted(default_perms.BaseCommentPermission):
    def is_authorized(self):
        return CanCommentConversation(
            request=self.request, obj=self.comment.conversation).is_authorized()


class OwnsComment(default_perms.BaseCommentPermission):
    def is_authorized(self):
        return self.comment.user_id == self.user.pk


CanCommentConversation = perms.Or(
    perms.And(
        ConversationIsOpen,
    ),
    perms.Or(OwnsConversation, otakantaa.IsModerator)
)

CanVoteComment = perms.And(
    perms.Not(CommentIsVotedByUser),
    CommentCanBeVoted
)

CanCancelVote = perms.And(
    CommentIsVotedByUser,
    ConversationIsOpen
)

CanRemoveComment = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(
        otakantaa.IsModerator,
        OwnsComment,
        OwnsConversation
    )
)

CanEditComment = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(
        otakantaa.IsModerator,
        OwnsConversation
    )
)
