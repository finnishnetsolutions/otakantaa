# coding=utf-8

from __future__ import unicode_literals

import json
from django.contrib.auth.models import Group
import pytz
import os
from unittest.case import skipUnless
from datetime import datetime, timedelta, date as ddate

from django.test.utils import override_settings
from django.utils import timezone
from django.core import mail
from django.conf import settings
from django.core.files.base import File, ContentFile
from django.utils.formats import date_format
from django.template.defaultfilters import date

from libs.attachtor.models.models import Upload, UploadGroup
from libs.attachtor.utils import get_upload_signature

from account.factories import UserFactory, DEFAULT_PASSWORD
from account.models import GROUP_NAME_MODERATORS
from conversation.factories import ConversationFactory, CommentFactory
from conversation.models import Comment, Vote
from organization.factories import OrganizationFactory
from organization.models import AdminSettings
from otakantaa.test.testcases import TestCase
from survey.factories import SurveyFactory, SurveySubmissionFactory, \
    SurveySubmitterFactory, SurveyQuestionFactory
from tagging.factories import TagFactory

from . import models
from .factories import SchemeFactory, ParticipationDetailsFactory, SchemeOwnersFactory
from .models import Scheme, ParticipationDetails
from .utils import warn_of_archiving, idle_schemes, archive_idle_schemes
from .tasks import archive_idle_schemes as archive_task, \
    warn_of_archiving as warn_task


class SchemeTest(TestCase):
    def test_schemes_view(self):
        resp = self.client.get("/fi/")
        self.assertTemplateUsed(resp, "scheme/schemes.html")
        self.assertTemplateUsed(resp, "scheme/scheme_boxes.html")

        self.assertContains(resp, "Osallistu keskusteluun. Vaikuta valmisteluun.", 1)
        self.assertContains(resp, "Otakantaa.fi-palvelusta löydät ajankohtaiset "
                                  "hankkeet, joihin kaivataan mielipidettäsi.", 1)

        self.assertContains(resp, "compact-search-component", 2)
        self.assertContains(resp, "extended-search-component", 3)
        self.assertContains(resp, "extended-search-components", 1)

        self.assertContains(resp, "id_text")
        self.assertContains(resp, "id_municipality")
        self.assertContains(resp, "id_tags")
        self.assertContains(resp, "id_organization")
        self.assertContains(resp, "id_status")
        self.assertContains(resp, "id_participations")
        self.assertContains(resp, "id_owner_type")
        self.assertContains(resp, "id_extended_search")
        self.assertContains(resp, "id_sorting")
        self.assertContains(resp, "id_display_type")

    def test_schemes_view_display_type_boxes(self):
        schemes = [SchemeFactory(), SchemeFactory()]
        resp = self.client.get("/fi/", {"display_type": "boxes"})
        self.assertTemplateUsed(resp, "scheme/scheme_boxes.html")
        self.assertTemplateNotUsed(resp, "scheme/scheme_list.html")
        self.assertContains(resp, schemes[0].title, 1)
        self.assertContains(resp, schemes[1].title, 1)

    def test_schemes_view_display_type_list(self):
        publish_date = datetime(2015, 3, 1, 12, 30, 0, 0, tzinfo=pytz.utc)
        schemes = [SchemeFactory(published=publish_date), SchemeFactory()]

        resp = self.client.get("/fi/", {"display_type": "list"})
        self.assertTemplateUsed(resp, "scheme/scheme_list.html")
        self.assertTemplateNotUsed(resp, "scheme/scheme_boxes.html")

        self.assertContains(resp, schemes[0].title, 1)
        self.assertContains(resp, schemes[1].title, 1)

        published_formatted = date_format(schemes[0].published, "SHORT_DATE_FORMAT")
        self.assertContains(resp, "Julkaistu: {}".format(published_formatted), 1)
        # no drafts in scheme search
        # self.assertContains(resp, "Luonnos", 1)

    def test_schemes_view_filter_text(self):
        schemes = [SchemeFactory(title="Scheming going on here"),
                   SchemeFactory(title="Nothing here", description="Some boring text.")]

        resp = self.client.get("/fi/", {"text": "going on"})
        self.assertTrue(resp.context["form"].is_valid(), resp.context["form"].errors)

        self.assertContains(resp, schemes[0].title)
        self.assertNotContains(resp, schemes[1].title)

        resp = self.client.get("/fi/", {"text": "BORING"})
        self.assertTrue(resp.context["form"].is_valid(), resp.context["form"].errors)

        self.assertNotContains(resp, schemes[0].title)
        self.assertContains(resp, schemes[1].title)

        resp = self.client.get("/fi/", {"text": "this text can't be found"})
        self.assertTrue(resp.context["form"].is_valid(), resp.context["form"].errors)

        self.assertNotContains(resp, schemes[0].title)
        self.assertNotContains(resp, schemes[1].title)

    def test_schemes_view_filter_status(self):
        schemes = [SchemeFactory(status=models.Scheme.STATUS_PUBLISHED),
                   SchemeFactory(status=models.Scheme.STATUS_CLOSED)]
        resp = self.client.get("/fi/", {"extended_search": True,
                                        "status": models.Scheme.STATUS_PUBLISHED})
        self.assertContains(resp, schemes[0].title)
        self.assertNotContains(resp, schemes[1].title)

        resp = self.client.get("/fi/", {"extended_search": True,
                                        "status": models.Scheme.STATUS_CLOSED})
        self.assertNotContains(resp, schemes[0].title)
        self.assertContains(resp, schemes[1].title)

    """
    def test_schemes_view_filter_organization(self):
        organizations = [OrganizationFactory(), OrganizationFactory()]
        schemes = [SchemeFactory(status=models.Scheme.STATUS_PUBLISHED,
                                 owner_organizations=[organizations[0]]),
                   SchemeFactory(status=models.Scheme.STATUS_CLOSED,
                                 owner_organizations=[organizations[1]])]
        resp = self.client.get("/fi/", {"extended_search": True,
                                        "organization": [organizations[0].pk]})
        self.assertContains(resp, schemes[0].title)
        self.assertNotContains(resp, schemes[1].title)

    def test_schemes_view_filter_owner_type(self):
        schemes = [SchemeFactory(),
                   SchemeFactory(owner_organizations=[OrganizationFactory()])]
        resp = self.client.get("/fi/", {"extended_search": True,
                                        "owner_type": "organization"})
        self.assertNotContains(resp, schemes[0].title)
        self.assertContains(resp, schemes[1].title)
    """

    def test_schemes_view_extended_search(self):
        """
        Assert extended search controls are not used to filter the results when
        extended_search is False.
        """
        scheme = SchemeFactory(status=models.Scheme.STATUS_PUBLISHED)
        resp = self.client.get("/fi/", {"extended_search": False,
                                        "status": models.Scheme.STATUS_CLOSED})
        self.assertContains(resp, scheme.title)

    def test_schemes_view_sorting_newest(self):
        reference_date = datetime(2015, 3, 1, 12, 30, tzinfo=pytz.utc)
        schemes = [
            SchemeFactory(published=reference_date - timedelta(days=5)),
            SchemeFactory(published=reference_date - timedelta(days=10)),
            SchemeFactory(published=reference_date - timedelta(days=1)),
        ]

        resp = self.client.get("/fi/", {"sorting": "newest"})
        object_list = list(resp.context["object_list"])
        self.assertEqual(object_list[0], schemes[2])
        self.assertEqual(object_list[1], schemes[0])
        self.assertEqual(object_list[2], schemes[1])


class SchemesPaginationTest(TestCase):
    def setUp(self):
        SchemeFactory.create_batch(35)

    def test_scheme_boxes_pagination_page_1(self):
        resp = self.client.get("/fi/")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 30)

    def test_scheme_boxes_pagination_page_2(self):
        resp = self.client.get("/fi/?page=2")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 35)

    def test_scheme_list_pagination_page_1(self):
        resp = self.client.get("/fi/?display_type=list")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 30)

    def test_scheme_list_pagination_page_2(self):
        resp = self.client.get("/fi/?page=2&display_type=list")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 35)

    def test_load_scheme_boxes_page_1(self):
        resp = self.client.get("/fi/hankkeet/lataa-lisaa/")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 30)
        self.assertTemplateUsed("scheme/scheme_boxes.html")
        self.assertTemplateUsed("scheme/scheme_boxes_results.html")

    def test_load_scheme_boxes_page_2(self):
        resp = self.client.get("/fi/hankkeet/lataa-lisaa/?page=2")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 35)
        self.assertTemplateUsed("scheme/scheme_boxes.html")
        self.assertTemplateUsed("scheme/scheme_boxes_results.html")

    def test_load_scheme_list_page_1(self):
        resp = self.client.get("/fi/hankkeet/lataa-lisaa/?display_type=list")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 30)
        self.assertTemplateUsed("scheme/scheme_list.html")

    def test_load_scheme_list_page_2(self):
        resp = self.client.get("/fi/hankkeet/lataa-lisaa/?page=2&display_type=list")
        object_list = list(resp.context["object_list"])
        self.assertEqual(len(object_list), 35)
        self.assertTemplateUsed("scheme/scheme_list.html")


class CreateSchemeAnonymousTest(TestCase):
    def test_anonymous_redirect(self):
        resp = self.client.get('/fi/hankkeet/uusi/', follow=True)
        self.assertContains(resp, 'Kirjaudu sisään tai rekisteröidy', status_code=200)


class TestCaseLoggedIn(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)


class CreateSchemeTest(TestCaseLoggedIn):
    def test_open_create_form(self):
        resp = self.client.get('/fi/hankkeet/uusi/')
        self.assertContains(resp, '<h1>Uusi hanke', status_code=200)
        self.assertNotContains(resp, '<div id="id_write_as_wrap" '
                               'class="form-group required">')

    def test_open_create_form_organization_admin(self):
        AdminSettings.objects.create(user=self.user, organization=OrganizationFactory())
        self.rehydrate(self.user)

        resp = self.client.get('/fi/hankkeet/uusi/')
        self.assertContains(resp, '<div id="id_write_as_wrap" '
                                  'class="form-group required">')
        self.assertContains(resp, '<option value="{}:{}" selected="selected">'.format(
            self.user.pk, self.user.organizations.first().pk
        ))


class ChangeSchemeStatusTest(TestCase):
    def test_publish(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        user = scheme.owners.first().user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        part1 = ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_DRAFT,
            content_object=ConversationFactory())

        survey = SurveyFactory()
        SurveyQuestionFactory(survey=survey)
        part2 = ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_PUBLISHED,
            content_object=survey)

        resp = self.client.post('/fi/hankkeet/%d/julkaise/' % scheme.pk, {}, follow=True)
        self.assertTemplateUsed(resp, 'scheme/scheme_detail.html')

        self.rehydrate(scheme)
        self.rehydrate(part1)
        self.rehydrate(part2)

        self.assertEqual(scheme.status, Scheme.STATUS_PUBLISHED)
        self.assertEqual(part1.status, ParticipationDetails.STATUS_PUBLISHED)
        self.assertEqual(part2.status, ParticipationDetails.STATUS_PUBLISHED)

    def test_publish_without_participations(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        user = scheme.owners.first().user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.post('/fi/hankkeet/%d/julkaise/' % scheme.pk, {}, follow=True)
        self.assertRedirects(resp, '/fi/hankkeet/%d/' % scheme.pk)
        self.assertNotContains(resp, "Hanke sekä siihen mahdollisesti liittyvät "
                                     "kyselyt ja keskustelut on julkaistu!")
        i2 = Scheme.objects.get(pk=scheme.pk)
        self.assertEqual(i2.status, Scheme.STATUS_DRAFT)
        self.assertEqual(i2.visibility, Scheme.VISIBILITY_DRAFT)
        self.assertIsNone(i2.published)

    def test_publish_without_survey_questions(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        participation = ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_DRAFT,
            content_object=SurveyFactory())
        user = scheme.owners.first().user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.post("/fi/hankkeet/{}/julkaise/".format(scheme.pk),
                                follow=True)
        self.assertContains(resp, "Kyselyssä '{}' ei ole yhtään kysymystä."
                            .format(participation.title))
        scheme.refresh_from_db(fields=["status", "visibility"])
        participation.refresh_from_db(fields=["status"])
        self.assertEqual(scheme.status, Scheme.STATUS_DRAFT)
        self.assertEqual(scheme.visibility, Scheme.VISIBILITY_DRAFT)
        self.assertEqual(participation.status, ParticipationDetails.STATUS_DRAFT)

    def test_publish_inactive_owner_organization(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        owner = scheme.owners.first()
        user = owner.user
        org = OrganizationFactory(admins=[user], is_active=False)

        owner.organization = org
        owner.save()

        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_DRAFT,
            content_object=ConversationFactory())

        resp = self.client.post('/fi/hankkeet/%d/julkaise/' % scheme.pk, {}, follow=True)
        self.assertTemplateUsed(resp, 'scheme/scheme_detail.html')
        self.assertContains(resp, "Hanketta ei voi vielä julkaista. Hankkeen omistajissa on "
                             "yhteyshenkilöitä tai organisaatioita, joita palvelun "
                             "ylläpitäjän ei ole hyväksynyt.")

        self.rehydrate(scheme)
        self.assertEqual(scheme.status, Scheme.STATUS_DRAFT)

    def test_publish_unapproved_owner_organization(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        owner = scheme.owners.first()
        user = owner.user
        org = OrganizationFactory(admins=[user], is_active=True)

        owner.organization = org
        owner.save()

        connection = AdminSettings.objects.get(user=user, organization=org)
        connection.approved = False
        connection.save()

        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_DRAFT,
            content_object=ConversationFactory())

        resp = self.client.post('/fi/hankkeet/%d/julkaise/' % scheme.pk, {}, follow=True)
        self.assertTemplateUsed(resp, 'scheme/scheme_detail.html')
        self.assertContains(resp, "Hanketta ei voi vielä julkaista. Hankkeen omistajissa on "
                             "yhteyshenkilöitä tai organisaatioita, joita palvelun "
                             "ylläpitäjän ei ole hyväksynyt.")

        self.rehydrate(scheme)
        self.assertEqual(scheme.status, Scheme.STATUS_DRAFT)

    def test_republish(self):
        scheme = SchemeFactory(status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)
        user = scheme.owners.first().user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.post('/fi/hankkeet/%d/julkaise/' % scheme.pk, {}, follow=True)
        self.assertRedirects(resp, '/fi/hankkeet/%d/' % scheme.pk)
        self.assertContains(resp, 'Hanke on jo julkaistu.')

    def test_revert_to_draft(self):
        scheme = SchemeFactory(status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)
        user = scheme.owners.first().user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        self.client.post('/fi/hankkeet/%d/muuta-luonnokseksi/' % scheme.pk)
        self.rehydrate(scheme)
        self.assertEqual(scheme.status, Scheme.STATUS_DRAFT)

    def test_revert_to_draft_when_participated(self):
        scheme = SchemeFactory(status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)
        conversation = ConversationFactory()
        ParticipationDetailsFactory.create(
            scheme=scheme, status=ParticipationDetails.STATUS_DRAFT,
            content_object=conversation)

        user = scheme.owners.first().user

        CommentFactory(conversation=conversation)

        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.post('/fi/hankkeet/%d/muuta-luonnokseksi/' % scheme.pk,
                                follow=True)
        self.assertRedirects(resp, '/fi/kayttaja/kirjaudu-sisaan/')
        self.assertContains(resp, 'Ei käyttöoikeutta')
        self.rehydrate(scheme)
        self.assertEqual(scheme.status, Scheme.STATUS_PUBLISHED)


class SchemeDetailTest(TestCase):
    def test_open_draft_as_owner(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        user = scheme.owners.all()[0].user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get('/fi/hankkeet/%d/' % scheme.pk)
        self.assertContains(resp, scheme.title, status_code=200)
        self.assertContains(resp, 'Julkaise hanke</a>')
        self.assertTemplateUsed(resp, 'scheme/scheme_detail.html')

    def test_open_draft_as_non_owner(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        user = UserFactory()
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get('/fi/hankkeet/%d/' % scheme.pk, follow=True)
        self.assertRedirects(resp, '/fi/')
        self.assertContains(resp, 'Hanke ei ole vielä julkinen.')

    def test_open_draft_as_guest(self):
        scheme = SchemeFactory(status=Scheme.STATUS_DRAFT,
                               visibility=Scheme.VISIBILITY_DRAFT)
        resp = self.client.get('/fi/hankkeet/%d/' % scheme.pk, follow=True)
        self.assertRedirects(resp, '/fi/kayttaja/kirjaudu-sisaan/?next=/fi/hankkeet/%d/'
                             % scheme.pk)
        self.assertContains(resp, 'Hanke ei ole vielä julkinen. '
                                  'Kirjaudu sisään, jos olet hankkeen omistaja.')

    def test_open_published_scheme_as_guest(self):
        scheme = SchemeFactory(title="Great Scheme #388", status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)
        resp = self.client.get('/fi/hankkeet/%d/' % scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<title>Hanke: Great Scheme #388')
        self.assertContains(resp, '<h1>Great Scheme #388')
        self.assertNotContains(resp, '/muokkaa/')
        self.assertNotContains(resp, 'Julkaise scheme')

    def test_open_published_scheme_as_owner(self):
        scheme = SchemeFactory(title="Great Scheme #388", status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)
        user = scheme.owners.all()[0].user
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get('/fi/hankkeet/%d/' % scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<h1>Great Scheme #388')
        self.assertContains(resp, '/fi/hankkeet/%d/muokkaa/' % scheme.pk, count=7)
        self.assertNotContains(resp, 'Julkaise hanke')


class SchemeDetailFragmentTest(TestCase):
    def setUp(self):
        self.scheme = SchemeFactory(
            title="My Tiiitle", description="My Deeescription")

    def test_open_detail_title_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/otsikko/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content/parts/scheme_detail_title.html')
        self.assertContains(resp, '<h1>My Tiiitle')
        self.assertNotContains(resp, "My Deeescription")
        self.assertNotContains(resp, "<form")

    def test_open_description_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/kuvaus/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content/parts/scheme_detail_description.html')
        self.assertNotContains(resp, 'My Tiiitle')
        self.assertContains(resp, "My Deeescription")
        self.assertNotContains(resp, "<form")

    def test_open_owners_fragment(self):
        # TODO: Add another owner. The page slices the first owner out on purpose.

        resp = self.client.get('/fi/hankkeet/%d/nayta/omistajat/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '@%s' % self.scheme.owners.first().user.username)
        self.assertNotContains(resp, 'My Tiiitle')

    def test_open_tags_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/aiheet/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '#%s' % self.scheme.tags.first().name)
        self.assertNotContains(resp, 'My Tiiitle')

    """
    def test_open_organizations_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/organisaatiot/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '%s</li>' % self.scheme.owner_organizations.first().
                            name)
        self.assertNotContains(resp, 'My Tiiitle')
    """

    def test_open_municipalities_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/kunnat/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '%s</li>' % self.scheme.target_municipalities.
                            first().name_fi)
        self.assertNotContains(resp, 'My Tiiitle')


class SchemeMainPictureTest(TestCase):
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'otakantaa', 'testdata', 'lolcat-sample.jpg')

    def setUp(self):
        self.scheme = SchemeFactory()
        user = self.scheme.owners.first().user
        self.client.login(username=user.username,
                          password=DEFAULT_PASSWORD)

    def test_upload_main_pic(self):
        self.assertRaises(ValueError, lambda: self.scheme.picture.file)
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/kuva/' % self.scheme.pk, {
            'picture': open(self.test_file, 'rb')
        })
        self.assertEqual(resp.status_code, 232)
        scheme2 = Scheme.objects.get(pk=self.scheme.pk)
        self.assertTrue(scheme2.picture.url.endswith('.jpg'))
        self.assertTrue(scheme2.picture_main.url.endswith('.jpg'))
        self.assertTrue(scheme2.picture_narrow.url.endswith('.jpg'))

    def test_open_edit_picture_fragment_no_existing_pic(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/kuva/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertTemplateUsed(resp, 'content/parts/scheme_edit_picture_form.html')
        self.assertContains(resp, "Uusi kuva")
        self.assertNotContains(resp, "Nykyinen kuva")
        self.assertNotContains(resp, '<img')
        self.assertNotContains(resp, "Poista kuva")

    def test_open_edit_picture_fragment_with_existing_pic(self):
        self.scheme.picture.save('lolcat.jpg', File(open(self.test_file, 'rb')))
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/kuva/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertTemplateUsed(resp, 'content/parts/scheme_edit_picture_form.html')
        self.assertContains(resp, "Uusi kuva")
        self.assertContains(resp, "Poista kuva")
        self.assertContains(resp, "Nykyinen kuva")
        self.assertContains(resp, '<img')
        self.assertContains(resp, self.scheme.picture_main.url)

    def test_open_picture_fragment_no_existing_pic(self):
        resp = self.client.get('/fi/hankkeet/%d/nayta/kuva/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/parts/scheme_detail_picture.html')
        self.assertContains(resp, 'Lisää otsikkokuva')
        self.assertNotContains(resp, '<img')

    def test_open_picture_fragment_with_existing_pic(self):
        self.scheme.picture.save('lolcat.jpg', File(open(self.test_file, 'rb')))
        resp = self.client.get('/fi/hankkeet/%d/nayta/kuva/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/parts/scheme_detail_picture.html')
        self.assertNotContains(resp, "no-picture-container-editable")
        self.assertContains(resp, '<img')
        self.assertContains(resp, self.scheme.picture_main.url)

    def tearDown(self):
        scheme = Scheme.objects.get(pk=self.scheme.pk)
        scheme.picture.delete()


class SchemeEditFragmentTest(TestCase):
    def setUp(self):
        self.scheme = SchemeFactory(title="My Tiiitle", description="My Deeescription")
        u = self.scheme.owners.first().user
        self.client.login(username=u.username, password=DEFAULT_PASSWORD)

    def login_as_moderator(self):
        self.client.logout()
        moderator = UserFactory(
            groups=[Group.objects.get(name=GROUP_NAME_MODERATORS)]
        )
        self.client.login(username=moderator.username, password=DEFAULT_PASSWORD)

    def test_open_edit_title_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/otsikko/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, 'value="My Tiiitle"')
        self.assertNotContains(resp, 'My Deeescription')

    def test_open_edit_description_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/kuvaus/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertNotContains(resp, 'My Tiiitle')
        self.assertContains(resp, "<form")
        self.assertContains(resp, "My Deeescription")

    def test_open_edit_owners_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, "<form")
        self.assertContains(
            resp, '>@%s</option>' % self.scheme.owners.first().user.username
        )
        self.assertNotContains(resp, 'My Tiiitle')

    """
    def test_open_edit_organizations_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/organisaatiot/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, "<form")
        self.assertContains(resp, '>%s</option>' %
                            self.scheme.owner_organizations.first().name)
        self.assertNotContains(resp, 'My Tiiitle')
    """
    def test_open_edit_tags_fragment(self):
        resp = self.client.get('/fi/hankkeet/%d/muokkaa/aiheet/' % self.scheme.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, "<form")
        self.assertContains(resp, '<select')
        self.assertContains(resp, '#%s</option>' % self.scheme.tags.first().name)
        self.assertNotContains(resp, 'My Tiiitle')

    def test_save_title_fragment(self):
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/otsikko/' % self.scheme.pk, {
            'title-fi': 'New Title'
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual('%s' % Scheme.objects.get(pk=self.scheme.pk).title, 'New Title')

    def test_save_description_fragment(self):
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/kuvaus/' % self.scheme.pk, {
            'description-fi': 'New Description',
            'upload_ticket': get_upload_signature()
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual('%s' % Scheme.objects.get(pk=self.scheme.pk).description,
                         'New Description')

    """
    def test_save_description_fragment_as_moderator_no_reason(self):
        self.login_as_moderator()
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/kuvaus/' % self.scheme.pk, {
            'description-fi': 'New Description',
            'upload_ticket': get_upload_signature()
        })
        self.assertEqual(resp.status_code, 200)
        self.assertRaises(ValueError, json.loads, resp.content)
        self.assertContains(resp, "Tämä kenttä vaaditaan.")

    def test_save_description_fragment_as_moderator_reason_given(self):
        self.login_as_moderator()
        self.assertEqual(ModerationReason.objects.count(), 0)
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/kuvaus/' % self.scheme.pk, {
            'description-fi': 'New Description',
            'upload_ticket': get_upload_signature(),
            '_moderation_reason': 'old description was rather naughty'
        })
        self.assertEqual(resp.status_code, 200)
        resp = json.loads(resp.content)
        self.assertTrue(resp['success'])
        self.assertEqual(resp['next'], '/fi/hankkeet/%d/nayta/kuvaus/' % self.scheme.pk)
        self.assertEqual('%s' % Scheme.objects.get(pk=self.scheme.pk).description,
                         'New Description')
        self.assertEqual(ModerationReason.objects.count(), 1)
        self.assertEqual(ModerationReason.objects.first().reason,
                         'old description was rather naughty')
    """

    def test_save_user_owners_fragment(self):
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [self.scheme.owners.first().user.pk, UserFactory().pk]
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 2)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': []
        })
        self.assertContains(resp, 'Et voi poistaa itseäsi hankkeen omistajista.')

    def test_save_user_owners_fragment_as_moderator(self):
        self.login_as_moderator()
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [self.scheme.owners.first().user.pk, UserFactory().pk],
            '_moderation_reason': 'any reason',
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 2)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [],
            '_moderation_reason': 'some reason',
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 0)

    def test_save_admin_owners_fragment(self):
        owner = self.scheme.owners.first()
        user = owner.user

        AdminSettings.objects.create(user=user, organization=OrganizationFactory())
        self.rehydrate(user)

        owner.organization = user.organizations.first()
        owner.save()

        user2 = UserFactory()
        AdminSettings.objects.create(user=user2, organization=OrganizationFactory())
        self.rehydrate(user2)

        self.assertEqual(self.scheme.written_as_organization(), True)

        value1 = "{}:{}".format(user.pk, user.organizations.first().pk)
        value2 = "{}:{}".format(user2.pk, user2.organizations.first().pk)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [value1, value2]
        })

        self.assertEqual(resp.status_code, 232)
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 2)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': []
        })
        self.assertContains(resp, 'Valitse hankkeen omistajat organisaatioiden '
                                  'yhteyshenkilöistä. Et voi poistaa itseäsi hankkeen '
                                  'omistajista.')

    def test_save_admin_owners_fragment_as_moderator(self):
        self.login_as_moderator()
        owner = self.scheme.owners.first()
        user = owner.user

        AdminSettings.objects.create(user=user, organization=OrganizationFactory())
        self.rehydrate(user)

        owner.organization = user.organizations.first()
        owner.save()

        user2 = UserFactory()
        AdminSettings.objects.create(user=user2, organization=OrganizationFactory())
        self.rehydrate(user2)

        self.assertEqual(self.scheme.written_as_organization(), True)

        value1 = "{}:{}".format(user.pk, user.organizations.first().pk)
        value2 = "{}:{}".format(user2.pk, user2.organizations.first().pk)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [value1, value2],
            '_moderation_reason': 'any reason',
        })

        self.assertEqual(resp.status_code, 232)
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 2)

        resp = self.client.post('/fi/hankkeet/%d/muokkaa/omistajat/' % self.scheme.pk, {
            'owners': [],
            '_moderation_reason': 'any reason',
        })
        self.assertEqual(Scheme.objects.get(pk=self.scheme.pk).owners.count(), 0)


    def test_save_tags_fragment(self):
        self.assertEqual(self.scheme.tags.count(), 1)
        resp = self.client.post('/fi/hankkeet/%d/muokkaa/aiheet/' % self.scheme.pk, {
            'tags': [self.scheme.tags.first().pk, TagFactory().pk]
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual(self.scheme.tags.count(), 2)


class SchemeAttachmentsTest(TestCase):

    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'otakantaa', 'testdata', 'lolcat-sample.jpg')

    def setUp(self):
        self.scheme = SchemeFactory()
        user = self.scheme.owners.first().user
        self.client.login(username=user.username,
                          password=DEFAULT_PASSWORD)

    def upload(self):
        return self.client.post('/fi/hankkeet/%d/liitteet/muokkaa/' % self.scheme.pk, {
            'files': open(self.test_file, 'rb')
        })

    def get_uploaded(self, upload=False):
        if upload:
            self.upload()
        scheme2 = Scheme.objects.get(pk=self.scheme.pk)
        return scheme2.attachments.first() or None

    def test_upload(self):
        resp = self.upload()
        self.assertEqual(resp.status_code, 232)
        self.assertTrue(self.get_uploaded().original_name.endswith('.jpg'))

    def test_list(self):
        file = self.get_uploaded(True)
        resp = self.client.get('/fi/hankkeet/%d/liitteet/nayta/' % self.scheme.pk)
        self.assertContains(
            resp, '<a href="/media/{}">{}</a>'.format(file.file, file.original_name), 1)

    def test_delete(self):
        file = self.get_uploaded(True)
        self.assertEqual(self.scheme.attachments.count(), 1)
        file.delete()
        self.assertEqual(self.scheme.attachments.count(), 0)

    def tearDown(self):
        scheme = Scheme.objects.get(pk=self.scheme.pk)
        for a in scheme.attachments.all():
            a.delete()


class CreateConversationTest(TestCase):
    def setUp(self):
        self.scheme = SchemeFactory(title="My Tiiitle", description="My Deeescription")
        u = self.scheme.owners.first().user
        self.client.login(username=u.username, password=DEFAULT_PASSWORD)

    def test_create_conversation_form(self):
        resp = self.client.get('/fi/hankkeet/%d/osallistuminen/keskustelu/uusi/' %
                               self.scheme.pk)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<h1>Uusi keskustelu</h1>')
        self.assertContains(resp, '<input', 6)

    def test_missing_fields(self):
        resp = self.client.post('/fi/hankkeet/%d/osallistuminen/keskustelu/uusi/' %
                                self.scheme.pk, {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tämä kenttä vaaditaan', 3)

    def test_create_conversation(self):
        resp = self.client.post('/fi/hankkeet/%d/osallistuminen/keskustelu/uusi/' %
                                self.scheme.pk,
                                {'title-fi': 'Heihou',
                                 'description-fi': 'Tämä on keskustelu',
                                 'scheme': self.scheme.pk,
                                 'expiration_date': date(
                                     datetime.now() +
                                     timedelta(days=2), 'SHORT_DATE_FORMAT'),
                                 'upload_ticket': get_upload_signature()},
                                follow=True)

        self.assertNotContains(resp, 'Täytä kaikki', status_code=200)
        obj = ParticipationDetails.objects.first()
        self.assertEqual(obj.is_conversation(), True)
        self.assertEqual(obj.status, ParticipationDetails.STATUS_DRAFT)


class CreateSurveyTest(TestCase):
    def setUp(self):
        self.scheme = SchemeFactory(title="My Tiiitle", description="My Deeescription")
        u = self.scheme.owners.first().user
        self.client.login(username=u.username, password=DEFAULT_PASSWORD)

    def test_create_survey_form(self):
        resp = self.client.get('/fi/hankkeet/%d/osallistuminen/kysely/uusi/' %
                               self.scheme.pk)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '<h1>Uusi kysely</h1>')
        self.assertContains(resp, '<input', 6)

    def test_missing_fields(self):
        resp = self.client.post('/fi/hankkeet/%d/osallistuminen/kysely/uusi/' %
                                self.scheme.pk, {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tämä kenttä vaaditaan', 3)

    def test_create_survey(self):
        resp = self.client.post('/fi/hankkeet/%d/osallistuminen/kysely/uusi/' %
                                self.scheme.pk,
                                {'title-fi': 'Heihou',
                                 'description-fi': 'Tämä on kysely',
                                 'scheme': self.scheme.pk,
                                 'expiration_date': date(
                                     datetime.now() +
                                     timedelta(days=2), 'SHORT_DATE_FORMAT'),
                                 'upload_ticket': get_upload_signature()},
                                follow=True)

        self.assertNotContains(resp, 'Täytä kaikki', status_code=200)
        obj = ParticipationDetails.objects.first()
        self.assertEqual(obj.is_survey(), True)
        self.assertEqual(obj.status, ParticipationDetails.STATUS_DRAFT)


class ParticipationDetailFragmentTest(TestCase):
    def setUp(self):
        self.participation = ParticipationDetailsFactory(
            title="My Tiiitle", description="My Deeescription",
            content_object=ConversationFactory(), expiration_date='2025-01-01')
        u = self.participation.scheme.owners.first().user
        self.client.login(username=u.username, password=DEFAULT_PASSWORD)

    def get_partial_detail_address(self, part):
        return '/fi/hankkeet/{}/osallistuminen/{}/nayta/{}/'.format(
            self.participation.scheme.pk, self.participation.pk, part)

    def test_open_detail_title_fragment(self):
        resp = self.client.get(self.get_partial_detail_address('otsikko'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content/parts/participation_detail_title.html')
        self.assertContains(resp, '<h1>My Tiiitle')
        self.assertNotContains(resp, "My Deeescription")
        self.assertNotContains(resp, "<form")

    def test_open_description_fragment(self):
        resp = self.client.get(self.get_partial_detail_address('kuvaus'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content/parts/participation_detail_description.html')
        self.assertNotContains(resp, 'My Tiiitle')
        self.assertContains(resp, "My Deeescription")
        self.assertNotContains(resp, "<form")

    def test_open_expiration_date_fragment(self):
        resp = self.client.get(self.get_partial_detail_address('paattymispaiva'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content/parts/participation_detail_expiration_date.html')
        self.assertNotContains(resp, 'My Tiiitle')
        self.assertContains(resp, ": </strong>{}".format('1.1.2025'))
        self.assertNotContains(resp, "<form")


class ParticipationEditFragmentTest(TestCase):
    def setUp(self):
        self.participation = ParticipationDetailsFactory(
            title="My Tiiitle", description="My Deeescription",
            content_object=ConversationFactory())
        u = self.participation.scheme.owners.first().user
        self.client.login(username=u.username, password=DEFAULT_PASSWORD)

    def get_partial_edit_address(self, part):
        return '/fi/hankkeet/{}/osallistuminen/{}/muokkaa/{}/'.format(
            self.participation.scheme.pk, self.participation.pk, part)

    """
    def login_as_moderator(self):
        mod = UserFactory(groups=[Group.objects.get(name=GROUP_NAME_MODERATORS)])
        self.client.login(username=mod.username, password=DEFAULT_PASSWORD)
        """

    '/fi/hankkeet/{}/osallistuminen/{}/muokkaa/'

    def test_open_edit_title_fragment(self):
        resp = self.client.get(self.get_partial_edit_address('otsikko'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, 'value="My Tiiitle"')
        self.assertNotContains(resp, 'My Deeescription')

    def test_open_edit_description_fragment(self):
        resp = self.client.get(self.get_partial_edit_address('kuvaus'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertNotContains(resp, 'My Tiiitle')
        self.assertContains(resp, "<form")
        self.assertContains(resp, "My Deeescription")

    def test_open_edit_expiration_date_fragment(self):
        resp = self.client.get(self.get_partial_edit_address('paattymispaiva'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'content/edit_base_form.html')
        self.assertContains(resp, "<form")
        self.assertContains(resp, '%s' % self.participation.expiration_date.date().
                            strftime('%d.%m.%Y'))

    def test_save_title_fragment(self):
        resp = self.client.post(self.get_partial_edit_address('otsikko'), {
            'title-fi': 'New Title'
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual('%s' % ParticipationDetails.objects.get(
            pk=self.participation.pk).title, 'New Title')

    def test_save_description_fragment(self):
        resp = self.client.post(self.get_partial_edit_address('kuvaus'), {
            'description-fi': 'New Description',
            'upload_ticket': get_upload_signature()
        })
        self.assertEqual(resp.status_code, 232)
        self.assertEqual('%s' % ParticipationDetails.objects.get(
            pk=self.participation.pk).description, 'New Description')

    def test_save_expiration_date_fragment(self):
        resp = self.client.post(self.get_partial_edit_address('paattymispaiva'), {
            'expiration_date': '15.3.2018'
        })
        # response code important
        self.assertEqual(resp.status_code, 205)
        self.assertEqual('%s' % ParticipationDetails.objects.get(
            pk=self.participation.pk).expiration_date, '2018-03-15')

    def test_save_equal_expiration_date_fragment(self):
        resp = self.client.post(self.get_partial_edit_address('paattymispaiva'), {
            'expiration_date': self.participation.expiration_date
        })
        # response code important
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            '%s' % ParticipationDetails.objects.get(
                pk=self.participation.pk).expiration_date,
            self.participation.expiration_date.date().strftime('%Y-%m-%d')
        )


class CommentTest(TestCase):
    def setUp(self):
        self.conversation = ConversationFactory()
        self.participation = ParticipationDetailsFactory(
            title="My Tiiitle", description="My Deeescription",
            content_object=self.conversation)

        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

    def test_comment_form(self):
        resp = self.client.get('/fi/keskustelut/{}/kommentit/'.
                               format(self.conversation.pk))
        self.assertContains(resp, '<input', 5, 200)

    def test_comment_form_anonymous(self):
        self.client.logout()
        resp = self.client.get('/fi/keskustelut/{}/kommentit/'.
                               format(self.conversation.pk))
        self.assertContains(resp, '<input', 6, 200)

    def test_comment_response_form(self):
        comment = CommentFactory(conversation=self.conversation)
        resp = self.client.get('/fi/keskustelut/{}/kommentti/{}/'.
                               format(self.conversation.pk, comment.pk))
        self.assertContains(resp, '<input', 4, 200)

    def test_comment_response_form_with_quote(self):
        comment = CommentFactory(conversation=self.conversation)
        comment2 = CommentFactory(conversation=self.conversation, comment="Quote this")
        resp = self.client.get('/fi/keskustelut/{}/kommentti/{}/lainaus/{}/'.
                               format(self.conversation.pk, comment.pk, comment2.pk))
        self.assertContains(resp, "var quote_pk = '{}';".format(comment2.pk), 1, 200)

    def test_comment_response_form_anonymous(self):
        self.client.logout()
        comment = CommentFactory(conversation=self.conversation)
        resp = self.client.get('/fi/keskustelut/{}/kommentti/{}/'.
                               format(self.conversation.pk, comment.pk))
        self.assertContains(resp, '<input', 5, 200)

    def test_post_comment(self):
        resp = self.client.post('/fi/keskustelut/{}/kommentoi/'.
                                format(self.conversation.pk),
                                {'title': "Test", 'comment': "Some text"})
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get('/fi/keskustelut/{}/kommentit/'.
                               format(self.conversation.pk))
        self.assertContains(resp, '<p class="comment-text">Some text</p>', 1, 200)

    def test_post_comment_response(self):
        comment = CommentFactory(conversation=self.conversation)
        resp = self.client.post('/fi/keskustelut/{}/vastaa/{}/'.
                                format(self.conversation.pk, comment.pk),
                                {'title': "Test response",
                                 'comment': "Some response text"})
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get('/fi/keskustelut/{}/kommentti/{}/'.
                               format(self.conversation.pk, comment.pk))
        self.assertContains(resp, 'class="comment-text">Some response text</p>', 1, 200)

    def test_sidebar_has_conversation_in_comment_and_responses_view(self):
        comment = CommentFactory(conversation=self.conversation)
        resp = self.client.get('/fi/keskustelut/{}/kommentti/{}/'.
                               format(self.conversation.pk, comment.pk))
        self.assertContains(resp, '<div class="participation-list-column">'
                                  'My Tiiitle', 1, 200)


class CommentVotingTest(TestCaseLoggedIn):

    def create_comment(self):
        pd = ParticipationDetailsFactory(content_object=ConversationFactory())
        return CommentFactory(conversation=pd.content_object)

    def test_vote_up(self):
        comment = self.create_comment()
        resp = self.client.post('/fi/keskustelut/{}/kannata/'.format(comment.pk))
        self.assertContains(resp, '<span class="thumbs-counter">+1</span>', 1, 200)
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)
        self.assertEqual(voted.votes.first().choice, Vote.VOTE_UP)

    def test_vote_down(self):
        comment = self.create_comment()
        resp = self.client.post('/fi/keskustelut/{}/vastusta/'.format(comment.pk))
        self.assertContains(resp, 'thumbs-counter negative">-1</span>', 1, 200)
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)
        self.assertEqual(voted.votes.first().choice, Vote.VOTE_DOWN)

    def test_vote_multiple_times_logged_in(self):
        comment = self.create_comment()
        self.client.post('/fi/keskustelut/{}/kannata/'.format(comment.pk))
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)
        self.client.post('/fi/keskustelut/{}/kannata/'.format(comment.pk))
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)

    def test_vote_multiple_times_anonymous(self):
        self.client.logout()
        comment = self.create_comment()
        resp = self.client.post('/fi/keskustelut/{}/kannata/'.format(comment.pk))
        self.assertEqual(resp.status_code, 200)
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)
        resp = self.client.post('/fi/keskustelut/{}/vastusta/'.format(comment.pk))
        self.assertEqual(resp.status_code, 302)
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)

    def test_vote_logged_in_and_after_logout(self):
        comment = self.create_comment()
        resp = self.client.post('/fi/keskustelut/{}/vastusta/'.format(comment.pk))
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 1)
        self.client.logout()
        resp = self.client.post('/fi/keskustelut/{}/vastusta/'.format(comment.pk))
        self.assertContains(resp, 'thumbs-counter negative">-2</span>', 1, 200)
        voted = Comment.objects.get(pk=comment.pk)
        self.assertEqual(voted.votes.count(), 2)


class SchemeExportTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.scheme = SchemeFactory(owners=[self.user])
        self.participations = [
            ParticipationDetailsFactory(scheme=self.scheme,
                                        content_object=ConversationFactory(),
                                        title="Very interesting conversation"),
            ParticipationDetailsFactory(scheme=self.scheme,
                                        content_object=SurveyFactory(),
                                        title="Fascinating questions"),
        ]

    def test_open_pdf_export_form(self):
        resp = self.client.get("/fi/hankkeet/{}/pdf/".format(self.scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "scheme/scheme_export_form.html")
        self.assertContains(resp, self.scheme.title)
        self.assertContains(resp, "Hankkeen lataaminen PDF-muodossa")
        self.assertContains(resp, "Hankkeen tiedot")
        self.assertContains(resp, "Valitse keskustelut")
        self.assertContains(resp, self.participations[0].title)
        self.assertContains(resp, "Valitse kyselyt")
        self.assertContains(resp, self.participations[1].title)
        self.assertContains(resp, "Lataa/Lähetä PDF-tiedosto")
        self.assertContains(resp, "Takaisin hankkeeseen")

    def test_pdf_export(self):
        resp = self.client.get(
            "/fi/hankkeet/{}/pdf/".format(self.scheme.pk),
            {
                "scheme_information": True,
                "conversations": [self.participations[0].pk],
                "surveys": [self.participations[1].pk],
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/pdf")
        self.assertEqual(resp.filename,
                         "otakantaa_{}.pdf".format(datetime.now().date()))

    def test_pdf_export_without_information(self):
        resp = self.client.get("/fi/hankkeet/{}/pdf/".format(self.scheme.pk),
                               {"scheme_information": False})
        self.assertContains(resp, "Hankkeen lataaminen PDF-muodossa")
        self.assertContains(resp, "Et valinnut mitään tietoja ladattavaksi.")

    def test_pdf_email_export(self):
        self.assertEqual(len(mail.outbox), 0)
        resp = self.client.get(
            "/fi/hankkeet/{}/pdf/".format(self.scheme.pk),
            {
                "scheme_information": True,
                "conversations": [self.participations[0].pk],
                "surveys": [self.participations[1].pk],
                "emails": ["teppo@testi.fi"]
            },
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp["content-type"], "application/pdf")
        self.assertRedirects(resp, "/fi/hankkeet/{}/".format(self.scheme.pk))
        self.assertContains(resp, "PDF-tiedosto lähetetty liitetiedostona.")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        self.assertEqual(mail.outbox[0].recipients()[0], 'teppo@testi.fi')
        self.assertEqual(mail.outbox[0].subject,
                         "Otakantaa.fi hanke: {}".format(self.scheme.title))
        self.assertFalse('{%' in mail.outbox[0].body)

    def test_open_excel_export_form(self):
        resp = self.client.get("/fi/hankkeet/{}/excel/".format(self.scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "scheme/scheme_export_form.html")
        self.assertTemplateUsed(resp, "scheme/scheme_export_excel_form.html")
        self.assertContains(resp, self.scheme.title)
        self.assertContains(resp, "Hankkeen lataaminen Excel-muodossa")
        self.assertContains(resp, "Keskustelut")
        self.assertContains(resp, self.participations[0].title)
        self.assertContains(resp, "Kyselyt")
        self.assertContains(resp, self.participations[1].title)
        self.assertContains(resp, "Lataa/Lähetä Excel-tiedosto")
        self.assertContains(resp, "Takaisin hankkeeseen")

    def test_conversation_excel_export(self):
        resp = self.client.get("/fi/hankkeet/{}/excel/".format(self.scheme.pk),
                               {"conversation": self.participations[0].pk})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/octet-stream")

    def test_survey_excel_export_without_submissions(self):
        resp = self.client.get("/fi/hankkeet/{}/excel/".format(self.scheme.pk),
                               {"survey": self.participations[1].pk})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/octet-stream")

    def test_survey_excel_export_with_submissions_with_user(self):
        SurveySubmissionFactory(submitter=SurveySubmitterFactory(user=UserFactory()),
                                survey=self.participations[1].content_object)
        resp = self.client.get("/fi/hankkeet/{}/excel/".format(self.scheme.pk),
                               {"survey": self.participations[1].pk})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/octet-stream")

    def test_survey_excel_export_with_submissions_without_user(self):
        SurveySubmissionFactory(survey=self.participations[1].content_object)
        resp = self.client.get("/fi/hankkeet/{}/excel/".format(self.scheme.pk),
                               {"survey": self.participations[1].pk})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/octet-stream")

    def test_excel_email_export(self):
        self.assertEqual(len(mail.outbox), 0)
        resp = self.client.get(
            "/fi/hankkeet/{}/excel/".format(self.scheme.pk),
            {
                "conversation": self.participations[0].pk,
                "emails": ["teppo@testi.fi"]
            },
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp["content-type"], "application/pdf")
        self.assertRedirects(resp, "/fi/hankkeet/{}/".format(self.scheme.pk))
        self.assertContains(resp, "Excel-tiedosto lähetetty liitetiedostona.")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        self.assertEqual(mail.outbox[0].recipients()[0], 'teppo@testi.fi')
        self.assertEqual(mail.outbox[0].subject,
                         "Otakantaa.fi hanke: {}".format(self.scheme.title))
        self.assertFalse('{%' in mail.outbox[0].body)

    def test_open_word_export_form(self):
        resp = self.client.get("/fi/hankkeet/{}/word/".format(self.scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "scheme/scheme_export_form.html")
        self.assertContains(resp, self.scheme.title)
        self.assertContains(resp, "Hankkeen lataaminen Word-muodossa")
        self.assertContains(resp, "Hankkeen tiedot")
        self.assertContains(resp, "Valitse keskustelut")
        self.assertContains(resp, self.participations[0].title)
        self.assertContains(resp, "Valitse kyselyt")
        self.assertContains(resp, self.participations[1].title)
        self.assertContains(resp, "Lataa/Lähetä Word-tiedosto")
        self.assertContains(resp, "Takaisin hankkeeseen")

    def test_word_export(self):
        resp = self.client.get(
            "/fi/hankkeet/{}/word/".format(self.scheme.pk),
            {
                "scheme_information": True,
                "conversations": [self.participations[0].pk],
                "surveys": [self.participations[1].pk],
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "text/docx")
        self.assertEqual(
            resp["content-disposition"],
            "attachment; filename=otakantaa_{}.docx".format(datetime.now().date())
        )

    def test_word_export_without_information(self):
        resp = self.client.get("/fi/hankkeet/{}/word/".format(self.scheme.pk),
                               {"scheme_information": False})
        self.assertContains(resp, "Hankkeen lataaminen Word-muodossa")
        self.assertContains(resp, "Et valinnut mitään tietoja ladattavaksi.")


class SchemeTwitterTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.scheme = SchemeFactory(owners=[self.user])

    def test_scheme_detail_has_twitter_feed_tool(self):
        resp = self.client.get("/fi/hankkeet/{}/".format(self.scheme.pk))
        self.assertContains(resp, "Työkalut")
        self.assertContains(resp, "Twitter-syöte")

    def test_open_scheme_detail_without_twitter_search(self):
        resp = self.client.get("/fi/hankkeet/{}/".format(self.scheme.pk))
        self.assertNotContains(resp, "twitter-logo")

    def test_open_scheme_detail_with_twitter_search(self):
        self.scheme.twitter_search = "helsinki"
        self.scheme.save()
        resp = self.client.get("/fi/hankkeet/{}/".format(self.scheme.pk))
        self.assertContains(resp, "twitter-logo")

    def test_open_scheme_twitter_search_form(self):
        resp = self.client.get(
            "/fi/hankkeet/{}/twitter-hakusana/".format(self.scheme.pk)
        )
        self.assertContains(resp, "Twitter-syöte")
        self.assertContains(resp, "Anna hakusana jolla hakea hankkeen Twitter-syötteen "
                            "tuloksia.")
        self.assertContains(resp, "Twitter-syöte tulee näkyviin hankkeen loppuosaan.")
        self.assertContains(resp, "Päivittymisessä voi kestää jonkin aikaa.")
        self.assertContains(resp, "Twitter-hakusana")
        self.assertContains(resp, "id_twitter_search")
        self.assertContains(resp, "Tallenna")
        self.assertContains(resp, "Peruuta")

    def test_post_scheme_twitter_search_form(self):
        resp = self.client.post("/fi/hankkeet/{}/twitter-hakusana/"
                                .format(self.scheme.pk), {"twitter_search": "testing"})
        self.assertRedirects(resp, "/fi/hankkeet/{}/".format(self.scheme.pk))
        self.scheme = Scheme.objects.get(pk=self.scheme.pk)
        self.assertEqual(self.scheme.twitter_search, "testing")


class ArchivingTest(TestCase):
    def setUp(self):
        self.warn_datetime = timezone.now() - timedelta(days=120 - 30)
        self.warn_date = self.warn_datetime.date()
        self.archive_date = self.reference_date = ddate.today() - timedelta(days=120)
        self.reference_datetime = timezone.now() - timedelta(days=120)
        self.before_datetime = self.warn_datetime - timedelta(days=60)
        self.after_datetime = self.warn_datetime + timedelta(days=10)

    def create_comment(self, scheme, create_date=None):
        pd = ParticipationDetailsFactory(scheme=scheme,
                                         content_object=ConversationFactory())
        return CommentFactory(conversation=pd.content_object,
                              created=create_date)

    def create_scheme_with_comment(self, comment_create_date=None, user_login_date=None,
                                   **kwargs):
        scheme = SchemeFactory(**kwargs)
        self.comment = self.create_comment(scheme, comment_create_date)
        owner = scheme.owners.first()
        u = owner.user

        if not user_login_date:
            user_login_date = timezone.now() - timedelta(days=90)
        u.last_login = user_login_date
        u.save()
        return scheme


class IdleSchemesTest(ArchivingTest):

    def test_fresh_comment(self):
        self.create_scheme_with_comment(self.after_datetime, self.after_datetime)
        schemes = list(idle_schemes(self.reference_date))
        self.assertListEqual(schemes, [])

    def test_old_comment(self):
        scheme = self.create_scheme_with_comment(self.before_datetime,
                                                 self.before_datetime)
        schemes = list(idle_schemes(self.reference_date))
        self.assertListEqual(schemes, [scheme])

    def test_old_comment_fresh_user(self):
        self.create_scheme_with_comment(self.before_datetime, timezone.now())
        schemes = list(idle_schemes(self.reference_date))
        self.assertListEqual(schemes, [])

    # todo: test submission

    # todo: test comment vote

    def test_status_draft(self):
        scheme = self.create_scheme_with_comment(self.before_datetime,
                                                 self.before_datetime)
        scheme.status = Scheme.STATUS_DRAFT
        scheme.save()
        schemes = idle_schemes(self.reference_date,
                               status=Scheme.STATUS_PUBLISHED,
                               visibility=Scheme.VISIBILITY_PUBLIC)

        self.assertListEqual(list(schemes), [])

    def test_status_published(self):
        scheme = self.create_scheme_with_comment(self.before_datetime,
                                                 self.before_datetime)
        schemes = idle_schemes(self.reference_date)
        self.assertListEqual(list(schemes), [scheme])

    def test_exact_date_with_exact_date(self):
        scheme = self.create_scheme_with_comment(self.reference_datetime,
                                                 self.reference_datetime)
        schemes = idle_schemes(self.reference_date, exact_date=True)
        self.assertQuerysetEqual(schemes, [repr(scheme)])

    def test_exact_date_with_older_date(self):
        self.create_scheme_with_comment(self.before_datetime, self.before_datetime)
        schemes = idle_schemes(self.reference_date, exact_date=True)
        self.assertQuerysetEqual(schemes, [])

    def test_exact_date_with_fresh_date(self):
        self.create_scheme_with_comment(self.after_datetime, self.after_datetime)
        schemes = idle_schemes(self.reference_date, exact_date=True)
        self.assertQuerysetEqual(schemes, [])

    def test_exact_date_with_exact_and_fresh_date(self):
        self.create_scheme_with_comment(self.reference_datetime, self.after_datetime)
        schemes = idle_schemes(self.reference_date, exact_date=True)
        self.assertQuerysetEqual(schemes, [])


class ArchiveIdleSchemesTest(ArchivingTest):
    """
    Couple of tests for the archive.
    Most functionality is already tested in IdleSchemesTest class.
    """

    def test_archive_idle_scheme(self):
        scheme = self.create_scheme_with_comment(self.before_datetime,
                                                 self.before_datetime)
        archive_idle_schemes(self.archive_date)
        scheme = Scheme.objects.get(pk=scheme.pk)
        self.assertEqual(scheme.visibility, Scheme.VISIBILITY_ARCHIVED)

    def test_archive_fresh_scheme(self):
        scheme = self.create_scheme_with_comment(self.after_datetime, self.after_datetime)
        archive_idle_schemes(self.archive_date)
        scheme = Scheme.objects.get(pk=scheme.pk)
        self.assertNotEqual(scheme.visibility, Scheme.VISIBILITY_ARCHIVED)


class ArchiveIdleSchemesTaskTest(ArchivingTest):
    """
    Couple of tests for the automatic archive task.
    Most functionality is already tested in IdleSchemesTest class.
    """

    def test_archive_idle_scheme(self):
        scheme = self.create_scheme_with_comment(self.before_datetime,
                                                 self.before_datetime)
        archive_task()
        scheme = Scheme.objects.get(pk=scheme.pk)
        self.assertEqual(scheme.visibility, Scheme.VISIBILITY_ARCHIVED)

    def test_archive_fresh_scheme(self):
        scheme = self.create_scheme_with_comment(self.after_datetime, self.after_datetime)
        archive_task()
        scheme = Scheme.objects.get(pk=scheme.pk)
        self.assertNotEqual(scheme.visibility, Scheme.VISIBILITY_ARCHIVED)


class WarnOfArchivingTest(ArchivingTest):
    """
    Couple of tests for the email warning.
    Most functionality is already tested in IdleSchemesTest class.
    """

    def test_warn_scheme_owners(self):
        scheme = self.create_scheme_with_comment(self.warn_datetime)
        owner = scheme.owners.first()

        self.assertEqual(len(mail.outbox), 0)
        warn_of_archiving(self.warn_date, self.archive_date)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        self.assertEqual(mail.outbox[0].recipients()[0], owner.user.settings.email)
        self.assertEqual(
            mail.outbox[0].subject,
            "Hankkeesi arkistoidaan 30 päivän kuluttua."
        )
        msg = "Otakantaa.fi hanke '{}' on ollut koskematon 90 päivää ja " \
              "päätetään automaattisesti 30 päivän kuluttua."
        self.assertTrue(msg.format(scheme.title) in mail.outbox[0].body)
        self.assertFalse('{%' in mail.outbox[0].body)

    def test_warn_several_owners(self):
        scheme = self.create_scheme_with_comment(self.warn_datetime)
        SchemeOwnersFactory(scheme=scheme)

        u = scheme.owners.last().user
        u.last_login = timezone.now() - timedelta(days=91)
        u.save()
        owners = scheme.owners.all()

        self.assertEqual(len(mail.outbox), 0)
        warn_of_archiving(self.warn_date, self.archive_date)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(len(mail.outbox[0].recipients()), 1)

        owner_emails = [owner.user.settings.email for owner in owners]
        recipient_emails = [x.recipients()[0] for x in mail.outbox]

        self.assertListEqual(owner_emails, recipient_emails)
        self.assertEqual(mail.outbox[0].recipients()[0], owners[0].user.settings.email)

    def test_fresh_scheme(self):
        self.create_scheme_with_comment(self.after_datetime)
        self.assertEqual(len(mail.outbox), 0)
        warn_of_archiving(self.warn_date, self.archive_date)
        self.assertEqual(len(mail.outbox), 0)

    def test_old_scheme(self):
        self.create_scheme_with_comment(self.before_datetime)
        self.assertEqual(len(mail.outbox), 0)
        warn_of_archiving(self.warn_date, self.archive_date)
        self.assertEqual(len(mail.outbox), 0)


class WarnOfArchivingTaskTest(ArchivingTest):
    """
    Couple of tests for the email warning task.
    Most functionality is already tested in IdleSchemesTest class.
    """

    def test_idle_scheme(self):
        self.create_scheme_with_comment(self.warn_datetime)
        self.assertEqual(len(mail.outbox), 0)
        warn_task()
        self.assertEqual(len(mail.outbox), 1)

    def test_fresh_scheme(self):
        self.create_scheme_with_comment(self.after_datetime)
        self.assertEqual(len(mail.outbox), 0)
        warn_task()
        self.assertEqual(len(mail.outbox), 0)

    def test_old_scheme(self):
        self.create_scheme_with_comment(self.before_datetime)
        self.assertEqual(len(mail.outbox), 0)
        warn_task()
        self.assertEqual(len(mail.outbox), 0)


@override_settings(CELERY_ALWAYS_EAGER=True)
class AttachmentUploadTest(TestCase):
    def setUp(self):
        self.upload_url = self.new_upload_url()

    def login(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

    def new_upload_url(self):
        return '/fi/liitteet/laheta/%s/' % get_upload_signature()

    def assert_upload_ok(self, resp, upload_count=None):
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse('error' in data)
        self.assertTrue('filelink' in data)
        self.assertTrue('filename' in data)

        if upload_count is not None:
            self.assertEqual(Upload.objects.count(), upload_count)

    def assert_upload_failed(self, resp, error_message=None, upload_count=None):
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue('error' in data)
        self.assertFalse('filelink' in data)
        self.assertFalse('filename' in data)

        if error_message is not None:
            self.assertEqual(data['error'], error_message)

        if upload_count is not None:
            self.assertEqual(Upload.objects.count(), upload_count)

    def tearDown(self):
        Upload.objects.all().delete()


class AnonymousAttachmentUploadTest(AttachmentUploadTest):

    def test_upload_attachment_not_logged_in(self):
        resp = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Upload.objects.count(), 0)


def attachment_settings(**kwargs):
    opts = settings.ATTACHMENTS.copy()
    opts.update(kwargs)
    return {'ATTACHMENTS': opts}


class LoggedInAttachmentUploadTest(AnonymousAttachmentUploadTest):
    def test_upload_ok(self):
        self.login()
        resp = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_ok(resp, upload_count=1)
        self.assertEqual(UploadGroup.objects.count(), 1)

    @override_settings(**attachment_settings(max_size=2))
    def test_single_file_size_limit(self):
        self.login()
        resp1 = self.client.post(self.upload_url, {
            'file': ContentFile('12', 'hi.txt')
        })
        self.assert_upload_ok(resp1)
        resp2 = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_failed(resp2, upload_count=1,
                                  error_message="Tiedosto ylittää kokorajoituksen.")

    @override_settings(**attachment_settings(max_attachments_per_object=2))
    def test_too_many_files_per_object(self):
        self.login()
        resp1 = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_ok(resp1)
        resp2 = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_ok(resp2)
        resp3 = self.client.post(self.upload_url, {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_failed(resp3, upload_count=2,
                                  error_message="Liian monta liitetiedostoa lisätty.")

        # We should still be able to attach files to another object.
        resp4 = self.client.post(self.new_upload_url(), {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_ok(resp4)

    @override_settings(**attachment_settings(max_size_per_uploader=4))
    def test_uploader_size_limit(self):
        self.login()
        resp1 = self.client.post(self.upload_url, {
            'file': ContentFile('12', 'hi.txt')
        })
        self.assert_upload_ok(resp1)
        resp2 = self.client.post(self.new_upload_url(), {
            'file': ContentFile('123', 'hi.txt')
        })
        self.assert_upload_failed(
            resp2, upload_count=1,
            error_message="Olet lisännyt liian monta liitetiedostoa. "
                          "Yritä myöhemmin uudestaan."
        )

        # We should still be able to upload as another user.
        user2 = UserFactory()
        self.client.login(username=user2.username, password=DEFAULT_PASSWORD)
        resp1 = self.client.post(self.new_upload_url(), {
            'file': ContentFile('1234', 'hi.txt')
        })

    def test_unallowed_extension(self):
        self.login()
        resp1 = self.client.post(self.upload_url, {
            'file': ContentFile('12', 'hi.exe')
        })
        self.assert_upload_failed(resp1, upload_count=0,
                                  error_message="Tiedostotyyppi ei ole sallittu.")

    def test_allowed_extension_uppercase(self):
        self.login()
        resp1 = self.client.post(self.upload_url, {
            'file': ContentFile('12', 'hi.TXT')
        })
        self.assert_upload_ok(resp1)


@skipUnless(settings.CLAMAV['enabled'], "ClamAV disabled")
class VirusUploadTest(AttachmentUploadTest):
    def test_virus_detected(self):
        self.login()
        resp = self.client.post(self.upload_url, {
            'file': ContentFile('X5O!P%@AP[4\PZX54(P^)7CC)7}'
                                '$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*', 'evil.txt')
        })
        self.assert_upload_failed(resp, upload_count=0,
                                  error_message="Tiedosto ei läpäissyt virustarkistusta. "
                                                "Löytynyt virus: Eicar-Test-Signature")

    def test_no_virus_detected(self):
        self.login()
        resp = self.client.post(self.upload_url, {
            'file': ContentFile('X5O!P%@AP[4\PZX54(P^)7CC)7}'
                                '$EIGAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*', 'evil.txt')
        })                        # ^ typo /s/C/G/ -> so it's obviously not a virus
        self.assert_upload_ok(resp)


class OpenSurveyTest(TestCase):
    def setUp(self):
        user = UserFactory()
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        self.scheme = SchemeFactory(owners=[user])
        self.survey = SurveyFactory()
        self.participation = ParticipationDetailsFactory(
            scheme=self.scheme,
            status=ParticipationDetails.STATUS_DRAFT,
            content_object=self.survey
        )

    def test_open_survey_without_questions(self):
        resp = self.client.post("/fi/hankkeet/{}/osallistuminen/{}/vaihda-tila/avaa/"
                                .format(self.scheme.pk, self.participation.pk),
                                follow=True)
        self.assertContains(resp, "Kyselyssä ei ole yhtään kysymystä.")
        self.participation.refresh_from_db(fields=["status"])
        self.assertEqual(self.participation.status, ParticipationDetails.STATUS_DRAFT)

    def test_open_survey_with_questions(self):
        self.survey.elements.add(SurveyQuestionFactory(survey=self.survey))
        resp = self.client.post("/fi/hankkeet/{}/osallistuminen/{}/vaihda-tila/avaa/"
                                .format(self.scheme.pk, self.participation.pk),
                                follow=True)
        self.assertNotContains(resp, "Kyselyssä ei ole yhtään kysymystä.",
                               status_code=200)
        self.participation.refresh_from_db(fields=["status"])
        self.assertEqual(self.participation.status, ParticipationDetails.STATUS_PUBLISHED)
