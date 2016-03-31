# coding=utf-8

from __future__ import unicode_literals
from datetime import datetime, timedelta

import factory

from account.factories import UserFactory

from . import models
from organization.factories import MunicipalityFactory
from tagging.factories import TagFactory


class SchemeFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda x: "A great scheme {}".format(x))
    description = "Let's go and do something fun."
    status = models.Scheme.STATUS_PUBLISHED
    visibility = models.Scheme.VISIBILITY_PUBLIC

    creator = factory.SubFactory(UserFactory)

    @factory.post_generation
    def owners(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for u in extracted:
                self.owners.add(SchemeOwnersFactory(scheme=self, user=u))
        else:
            self.owners.add(SchemeOwnersFactory(scheme=self, user=self.creator))

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.tags.add(*extracted)
        else:
            self.tags.add(TagFactory())

    @factory.post_generation
    def target_municipalities(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.target_municipalities.add(*extracted)
        else:
            self.target_municipalities.add(MunicipalityFactory())

    class Meta:
        model = models.Scheme


class SchemeOwnersFactory(factory.DjangoModelFactory):
    scheme = None
    organization = None
    user = factory.SubFactory('account.factories.UserFactory')
    approved = True

    class Meta:
        model = models.SchemeOwner


class ParticipationDetailsFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.ParticipationDetails

    title = factory.Sequence(lambda x: "A great participation {}".format(x))
    description = "Let's fun and do something go."
    status = models.ParticipationDetails.STATUS_PUBLISHED
    expiration_date = datetime.today() + timedelta(7)

    content_object = None

    scheme = factory.SubFactory('content.factories.SchemeFactory')
