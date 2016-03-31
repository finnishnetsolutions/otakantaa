# coding=utf-8

from __future__ import unicode_literals
from datetime import datetime

from django.contrib.auth.models import Group
from django.utils.translation import override
from django.utils import timezone

from libs.attachtor.utils import get_upload_signature

from otakantaa.test.testcases import TestCase
from account.factories import UserFactory, DEFAULT_PASSWORD
from account.models import GROUP_NAME_MODERATORS
from organization.factories import OrganizationFactory, MunicipalityFactory
from organization.models import Organization


class CreateOrganizationTest(TestCase):
    def setUp(self):
        # HACK: setup Organization.unmoderated_objects manager
        # from libs.moderation.helpers import auto_discover
        # auto_discover()

        self.user = UserFactory()
        self.client.login(username=self.user.username,
                          password=DEFAULT_PASSWORD)

    def test_load_create_form(self):
        resp = self.client.get('/fi/organisaatiot/uusi/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Uusi organisaatio")

    def test_create(self):
        # self.assertEqual(Organization.unmoderated_objects.real().count(), 0)
        self.assertEqual(Organization.objects.all().count(), 0)
        resp = self.client.post('/fi/organisaatiot/uusi/', {
            'name-fi': 'Test Oy',
            'name-sv': 'Test Ab',
            'type': Organization.TYPE_ORGANIZATION,
            'municipalities': [],
            'admins': [self.user.pk, ],
            'description-fi': 'tadaa',
            'terms_accepted': True,
            'upload_ticket': get_upload_signature()
        })
        self.assertEqual(resp.status_code, 302)
        # self.assertEqual(Organization.unmoderated_objects.real().count(), 1)
        self.assertEqual(Organization.objects.all().count(), 1)
        # org = Organization.unmoderated_objects.real().first()
        org = Organization.objects.all().first()

        self.assertEqual('%s' % org.name, 'Test Oy')
        self.assertEqual('%s' % org.description, 'tadaa')
        with override(language='sv'):
            self.assertEqual('%s' % org.name, 'Test Ab')
            self.assertEqual('%s' % org.description, 'tadaa')

        self.assertEqual(len(org.admins.all()), 1)
        self.assertEqual(self.user.pk, org.admins.first().pk)
        self.assertEqual(org.municipalities.count(), 0)
        self.assertFalse(org.is_active)

    def test_create_municipality(self):
        # self.assertEqual(Organization.unmoderated_objects.real().count(), 0)
        self.assertEqual(Organization.objects.all().count(), 0)
        resp = self.client.post('/fi/organisaatiot/uusi/', {
            'name-sv': 'Test Org',
            'type': Organization.TYPE_PUBLIC_ADMINISTRATION,
            'municipalities': [MunicipalityFactory().pk],
            'admins': [self.user.pk, ],
            'description-fi': 'tadaa',
            'description-sv': 'wohoo',
            'terms_accepted': True,
            'upload_ticket': get_upload_signature()
        })
        self.assertEqual(resp.status_code, 302)
        # self.assertEqual(Organization.unmoderated_objects.real().count(), 1)
        self.assertEqual(Organization.objects.all().count(), 1)
        # org = Organization.unmoderated_objects.real().first()
        org = Organization.objects.all().first()
        self.assertEqual('%s' % org.name, 'Test Org')
        self.assertEqual('%s' % org.description, 'tadaa')
        with override(language='fi'):
            self.assertEqual('%s' % org.name, 'Test Org')
            self.assertEqual('%s' % org.description, 'tadaa')
        with override(language='sv'):
            self.assertEqual('%s' % org.name, 'Test Org')
            self.assertEqual('%s' % org.description, 'wohoo')
        with override(language='en'):
            self.assertEqual('%s' % org.name, 'Test Org')
            self.assertEqual('%s' % org.description, 'tadaa')
        self.assertEqual(org.municipalities.count(), 1)


class OrganizationDetailTest(TestCase):
    def test_organization_detail_visitor(self):
        org = OrganizationFactory()
        resp = self.client.get('/fi/organisaatiot/%d/' % org.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<h1>%s' % org.name)
        self.assertNotContains(resp, 'fa-edit')

    def test_organization_detail_org_admin(self):
        user = UserFactory()
        org = OrganizationFactory(admins=[user, ])
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get('/fi/organisaatiot/%d/' % org.pk)
        self.assertTemplateUsed(resp, 'organization/organization_detail.html')
        self.assertTemplateUsed(resp, 'organization/organization_detail_description.html')
        self.assertContains(resp, 'fa-edit', count=4)


class ActivatingOrganizationTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.org = OrganizationFactory(admins=[self.user, ])
        self.client.login(username=self.user.username,
                          password=DEFAULT_PASSWORD)

    def test_activate_organization_when_not_admin(self):
        other_user = UserFactory()
        other_org = OrganizationFactory(admins=[other_user, ],
                                        activated=timezone.now())

        resp = self.client.get('/fi/organisaatiot/{}/'.format(other_org.pk))
        # test activation link not exists
        self.assertNotContains(
            resp, '<div class="dropdown organization-tools-wrap pull-right">')

        other_org.is_active = False
        other_org.save()
        resp = self.client.post('/fi/organisaatiot/{}/aktivoi/'.format(other_org.pk),
                                follow=True)
        self.assertContains(resp, 'Ei käyttöoikeutta.')
        self.assertEqual(other_org.is_active, False)

    def test_activate_organization(self):
        self.org.is_active = False
        self.org.save()
        self.assertEqual(self.org.awaits_activation(), True)
        resp = self.client.get('/fi/organisaatiot/{}/'.format(self.org.pk))
        # test activation link not exists
        self.assertNotContains(
            resp, '<div class="dropdown organization-tools-wrap pull-right">')
        resp = self.client.post('/fi/organisaatiot/{}/aktivoi/'.format(self.org.pk),
                                follow=True)
        self.assertContains(resp, 'Ei käyttöoikeutta.')

        self.org.activated = timezone.now()
        self.org.save()
        resp = self.client.get('/fi/organisaatiot/{}/'.format(self.org.pk))
        self.assertContains(resp, 'Organisaatio on piilotettu.')

        resp = self.client.post('/fi/organisaatiot/{}/aktivoi/'.format(self.org.pk),
                                follow=True)
        self.assertEqual(resp.status_code, 231)
        self.rehydrate(self.org)
        self.assertEqual(self.org.is_active, True)

    def test_activate_organization_moderator(self):
        self.user.groups.add(Group.objects.get(name=GROUP_NAME_MODERATORS))

        is_moderator = True if self.user.is_moderator else False
        self.assertEqual(is_moderator, True)

        self.org.is_active = False
        self.org.save()

        resp = self.client.get('/fi/organisaatiot/{}/'.format(self.org.pk))
        self.assertContains(resp, 'Odottaa ylläpitäjän hyväksyntää.')
        self.assertContains(
            resp, '<div class="dropdown organization-tools-wrap pull-right">')
        resp = self.client.post('/fi/organisaatiot/{}/aktivoi/'.format(self.org.pk),
                                follow=True)
        self.rehydrate(self.org)
        self.assertEqual(self.org.is_active, True)


class OrganizationListTest(TestCase):
    def test_list(self):
        org = OrganizationFactory()
        resp = self.client.get('/fi/organisaatiot/')
        self.assertContains(resp, org.name)

    def test_list_not_showing_hidden_organizations(self):
        org = OrganizationFactory()
        OrganizationFactory()
        resp = self.client.get('/fi/organisaatiot/')
        self.assertContains(resp, '<article class="scheme-box">', 2)

        org.is_active = False
        org.save()
        resp = self.client.get('/fi/organisaatiot/')
        self.assertContains(resp, '<article class="scheme-box">', 1)


class OrganizationTwitterTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.organization = OrganizationFactory(admins=[self.user])

    def test_organization_detail_has_twitter_feed_tool(self):
        resp = self.client.get("/fi/organisaatiot/{}/".format(self.organization.pk))
        self.assertContains(resp, "Työkalut")
        self.assertContains(resp, "Twitter-syöte")

    def test_open_organization_detail_without_twitter_search(self):
        resp = self.client.get("/fi/organisaatiot/{}/".format(self.organization.pk))
        self.assertNotContains(resp, "twitter-logo")

    def test_open_organization_detail_with_twitter_search(self):
        self.organization.twitter_username = "twituser"
        self.organization.save()
        resp = self.client.get("/fi/organisaatiot/{}/".format(self.organization.pk))
        self.assertContains(resp, "twitter-logo")

    def test_open_organization_twitter_search_form(self):
        resp = self.client.get(
            "/fi/organisaatiot/{}/twitter-kayttajanimi/".format(self.organization.pk)
        )
        self.assertContains(resp, "Twitter-syöte")
        self.assertContains(resp, "Twitter-syöte tulee näkyviin organisaatiosivun "
                            "loppuosaan.")
        self.assertContains(resp, "Päivittymisessä voi kestää jonkin aikaa.")
        self.assertContains(resp, "Twitter-käyttäjänimi")
        self.assertContains(resp, "id_twitter_username")
        self.assertContains(resp, "Tallenna")
        self.assertContains(resp, "Peruuta")

    def test_post_organization_twitter_search_form(self):
        resp = self.client.post("/fi/organisaatiot/{}/twitter-kayttajanimi/"
                                .format(self.organization.pk),
                                {"twitter_username": "random_user"})
        self.assertRedirects(resp, "/fi/organisaatiot/{}/".format(self.organization.pk))
        self.organization = Organization.objects.get(pk=self.organization.pk)
        self.assertEqual(self.organization.twitter_username, "random_user")
