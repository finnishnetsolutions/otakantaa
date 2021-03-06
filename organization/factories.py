# coding=utf-8

from __future__ import unicode_literals

import datetime
import factory

from account.factories import UserFactory
from libs.fimunicipality.models import Municipality

from .models import Organization
from organization.models import AdminSettings


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Organization

    type = Organization.TYPE_ORGANIZATION
    name = factory.Sequence(lambda n: 'Test organization #{0:d}'.format(n))
    is_active = True
    activated = None

    @factory.post_generation
    def admins(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            for admin in extracted:
                AdminSettings.objects.create(
                    user=admin,
                    organization=self
                )
        else:
            AdminSettings.objects.create(
                user=UserFactory(),
                organization=self
            )


MUNICIPALITIES_FI = ('Espoo', 'Vantaa', 'Lahti', 'Helsinki', 'Tampere',)
MUNICIPALITIES_SV = ('Esbo', 'Vanda', 'Lahti', 'Helsingfors', 'Tammerfors',)


class MunicipalityFactory(factory.DjangoModelFactory):
    class Meta:
        model = Municipality

    name_fi = factory.Sequence(lambda n: MUNICIPALITIES_FI[n % len(MUNICIPALITIES_SV)])
    name_sv = factory.Sequence(lambda n: MUNICIPALITIES_SV[n % len(MUNICIPALITIES_FI)])
    code = factory.Sequence(lambda n: '%03d' % (200 + n))

    beginning_date = datetime.date(1900, 01, 01)
    expiring_date = datetime.date(2050, 12, 31)
    created_date = datetime.date(1975, 01, 01)
    last_modified_date = datetime.date(1975, 01, 01)
