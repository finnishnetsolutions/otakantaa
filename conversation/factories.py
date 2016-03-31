# coding=utf-8

from __future__ import unicode_literals

import factory
from django.utils import timezone

from . import models


class ConversationFactory(factory.DjangoModelFactory):
    @factory.post_generation
    def comments(self, create, extracted, **kwargs):
        if extracted:
            self.comments.add(*extracted)

    class Meta:
        model = models.Conversation


class CommentFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda x: "This is comment number {}".format(x))
    comment = "Trying to come up with something clever"
    user = None
    user_name = factory.Sequence(lambda x: "Guest {}".format(x))
    conversation = None
    created = timezone.now()

    class Meta:
        model = models.Comment
