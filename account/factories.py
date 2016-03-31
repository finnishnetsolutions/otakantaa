# coding=utf-8

from __future__ import unicode_literals

import factory

from django.utils import timezone

from .models import User, UserSettings, ClientIdentifier


DEFAULT_PASSWORD = 'letsgo123!'


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    status = User.STATUS_ACTIVE
    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    password = factory.PostGenerationMethodCall('set_password', DEFAULT_PASSWORD)
    settings = factory.RelatedFactory('account.factories.UserSettingsFactory', "user")
    last_login = factory.LazyAttribute(lambda a: timezone.now())

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class UserSettingsFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserSettings

    user = factory.SubFactory(UserFactory, settings=None)
    email = factory.Sequence(lambda n: 'tester_{0}@test.dev'.format(n))
    municipality = factory.SubFactory('organization.factories.MunicipalityFactory')


class ClientIdentifierFactory(factory.DjangoModelFactory):
    ip = "127.0.0.1"
    user_agent = "some-agent"
    hash = factory.Sequence(lambda n: "secret-hash-{}".format(n))

    class Meta:
        model = ClientIdentifier
