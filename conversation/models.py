# coding=utf-8

from __future__ import unicode_literals
from datetime import datetime

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from actions.models import ActionGeneratingModelMixin
from content.models import ParticipationDetails


class Conversation(models.Model):
    def public_comments(self):
        return self.comments.public()

    def public_comments_filter_removed(self):
        return self.comments.public()

    def get_parent_scheme(self):
        return self.get_parent_participation().scheme

    def get_parent_participation(self):
        return ParticipationDetails.objects.get(
            content_type=ContentType.objects.get_for_model(Conversation),
            object_id=self.pk
        )

    def get_involved_user_ids(self):
        return self.comments.filter(user__isnull=False).values_list('user_id', flat=True)

    def last_participation_date(self):
        if self.comments.count():
            commented_on = self.comments.order_by('created').last().created.date()
            comments_pk_list = self.comments.all().values_list('pk', flat=True)
            last_vote = Vote.objects.filter(
                content_type=ContentType.objects.get_for_model(Comment),
                object_id__in=comments_pk_list
            ).order_by('created').last()
            if last_vote and last_vote.created.date() > commented_on:
                return last_vote.created.date()
            else:
                return commented_on
        return datetime.min.date()


COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)


class CommentQuerySet(QuerySet):

    # excludes responses
    def comments(self):
        return self.filter(target_comment__isnull=True).public()

    def prefetch(self):
        return self.prefetch_related('user__settings')

    def public(self):
        # if self.count():
        #     scheme = self.first().conversation.get_parent_scheme()
        #     if scheme.premoderation is True:
        return self.filter(is_public=True)

    def filter_removed(self):
        # if self.count():
        #     scheme = self.first().conversation.get_parent_scheme()
        #     if scheme.premoderation is True:
        return self.filter(is_removed=False)

    def visible(self):
        return self.public().exclude(is_removed=True)


@python_2_unicode_compatible
class Comment(ActionGeneratingModelMixin, models.Model):

    conversation = models.ForeignKey(Conversation, related_name='comments', null=True)
    quote = models.ForeignKey('self', null=True, blank=True, related_name='quoted')
    target_comment = models.ForeignKey('self', null=True, blank=True,
                                       related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             related_name='comments')
    user_name = models.CharField(_("nimimerkki"), max_length=50, blank=True)
    title = models.CharField(_("otsikko"), max_length=255, blank=True)
    comment = models.TextField(_("kommentti"), max_length=COMMENT_MAX_LENGTH, default='')
    created = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    is_removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey('account.User', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    votes = GenericRelation('Vote', related_query_name='comments')
    admin_comment = models.BooleanField(default=False)
    objects = CommentQuerySet.as_manager()

    @cached_property
    def name(self):
        return self.user or self.user_name

    def is_anonymous(self):
        return self.user_id is None

    def is_response(self):
        return True if self.target_comment else False

    def voter_user_ids(self):
        return [x.voter.user_id for x in self.votes.all() if x.voter.user_id]

    def __str__(self):
        return "%s: %s..." % (self.name, self.comment[:50])

    def get_absolute_url(self):
        pk = self.target_comment.pk if self.is_response() else self.pk
        return reverse('conversation:comment_detail', kwargs={
            'conversation_id': self.conversation_id, 'comment_id': pk
        })

    # for moderation
    @property
    def owner_ids(self):
        return [self.user.pk] if self.user_id else []

    def action_kwargs_on_create(self):
        return {'actor': self.user}

    def fill_notification_recipients(self, action):
        self.conversation.get_parent_scheme().fill_notification_recipients(action)

    class Meta:
        ordering = ('created', )


class Voter(models.Model):
    VOTER_COOKIE = "joku"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, default=None)
    voter_id = models.CharField(max_length=32, unique=True)
    created = models.DateTimeField(default=timezone.now)


class VoteQuerySet(models.QuerySet):
    def up(self):
        return self.filter(choice=Vote.VOTE_UP)

    def down(self):
        return self.filter(choice=Vote.VOTE_DOWN)

    def balance(self):
        balance = sum([vote.choice for vote in self])
        return '+{}'.format(balance) if balance > 0 else balance

    def filter(self, *args, **kwargs):
        if 'content_object' in kwargs:
            content_object = kwargs.pop('content_object')
            content_type = ContentType.objects.get_for_model(content_object)
            kwargs.update({
                'content_type': content_type,
                'object_id': content_object.pk
            })
        return super(VoteQuerySet, self).filter(*args, **kwargs)


class Vote(models.Model):
    VOTE_UP = 1
    VOTE_DOWN = -1
    VOTE_NONE = 0

    voter = models.ForeignKey(Voter)
    client_identifier = models.ForeignKey('account.ClientIdentifier')

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    created = models.DateTimeField(auto_now_add=True)
    choice = models.SmallIntegerField()

    objects = VoteQuerySet.as_manager()

    @classmethod
    def votes_for(cls, model, instance=None):
        ct = ContentType.objects.get_for_model(model)
        kwargs = {'content_type': ct}
        if instance is not None:
            kwargs['object_id'] = instance.pk
        return cls.objects.filter(**kwargs)

    class Meta:
        unique_together = ('voter', 'content_type', 'object_id')
