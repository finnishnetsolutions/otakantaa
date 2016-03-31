# coding=utf-8

from __future__ import unicode_literals

from account.factories import UserFactory, DEFAULT_PASSWORD

from content.factories import SchemeFactory
from otakantaa.test.testcases import TestCase


class SurveyTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.scheme = SchemeFactory(owners=[self.user])

    def test_open_create_form(self):
        resp = self.client.get(
            "/fi/hankkeet/{}/osallistuminen/kysely/uusi/".format(self.scheme.pk)
        )
        self.assertTemplateUsed(resp, "participation/create_survey_form.html")
        self.assertContains(resp, "Uusi kysely")
        self.assertContains(resp, "Täytä kyselyn perustiedot")
        self.assertContains(resp, "Kieliversiot")
        self.assertContains(resp, "id_title")
        self.assertContains(resp, "id_description")
        self.assertContains(resp, "id_expiration_date")
        self.assertContains(resp, "Tallenna kysely")

    """
    def test_create_survey(self):
        resp = self.client.post(
            "/fi/hankkeet/{}/osallistuminen/kysely/uusi/".format(self.scheme.pk),
            {
                "scheme": self.scheme.pk,
                "title": "Difficult questions inside",
                "description": "Try to answer these.",
                "expiration_date": "2015-03-10"
            },
            follow=True
        )
        # TODO: Set upload_ticket somehow.
        print "=== create_survey ==="
        print resp
        self.assertTrue(resp.context["form"].is_valid(), resp.context["form"].errors)
        self.assertContains(resp, "Difficult questions inside")
        self.assertContains(resp, "Try to answer these.")
        self.assertContains(resp, "Luonnos 10.3.2015")
        self.assertContains(resp, "Muokkaa kyselyä")

        survey = models.Survey.objects.first()
        self.assertIsNotNone(survey)
        self.assertEqual(survey.title, "Difficult questions inside")
        self.assertEqual(survey.description, "Try to answer these.")
        self.assertEqual(survey.expiration_date, "2015-03-10")
    """

    """
    def test_open_draft_logged_out(self):
        self.client.logout()
        survey = SurveyFactory()
        resp = self.client.get("/fi/hankkeet/{}/osallistuminen/kysely/{}/",
                               {"scheme_id": self.scheme.pk, "survey_id": survey.pk})

    def test_open_draft_logged_in_as_non_owner(self):
        pass

    def test_open_draft_logged_in_as_owner(self):
        self.scheme.owners.add(self.user)

    def test_open_edit_mode_as_non_owner(self):
        pass

    def test_open_edit_mode_as_owner(self):
        pass

    def test_open_edit_mode_with_submissions(self):
        pass

    def test_move_element_up(self):
        survey = SurveyFactory()
        elements = [
            ParticipationDetailsFactory(content_object=SchemeFactory()),
            ParticipationDetailsFactory(content_object=SchemeFactory()),
            ParticipationDetailsFactory(content_object=SchemeFactory()),
        ]

    def test_move_element_down(self):
        pass

    def test_delete_element(self):
        pass

    def test_create_page(self):
        pass

    def test_create_subtitle(self):
        pass

    def test_update_subtitle(self):
        pass
    """
