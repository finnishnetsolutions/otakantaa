# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta
import os

from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings
from django.core.files.base import File

from content.factories import SchemeFactory, SchemeOwnersFactory
from content.models import Scheme
from otakantaa.test.testcases import TestCase
from organization.factories import MunicipalityFactory, OrganizationFactory

from .factories import UserFactory, UserSettingsFactory
from .forms import EmailConfirmationForm
from .models import User, UserSettings, GROUP_NAME_ADMINS, GROUP_NAME_MODERATORS
from .factories import DEFAULT_PASSWORD


@override_settings(SMS={'enabled': False})
class SignupTest(TestCase):

    def setUp(self):
        self.municipality = MunicipalityFactory(name_fi='Espoo')

    def register_user(self, follow=True):
        response = self.client.post('/fi/kayttaja/rekisteroidy/', {
            'user-username': 'meme',
            'user-password1': 'testi123',
            'user-password2': 'testi123',
            'usersettings-first_name': 'Teppo',
            'usersettings-last_name': 'Testaaja',
            'usersettings-email': 'me@example.com',
            'usersettings-municipality': str(self.municipality.pk),
            'usersettings-language': 'fi',
        }, follow=follow)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Valitse oikea vaihtoehto')
        return {'response': response}

    def test_rekisteroitymisvalintalomakkeen_avaaminen(self):
        resp = self.client.get('/fi/kayttaja/valitse-rekisteroitymistapa/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Rekisteröidy')
        self.assertTemplateUsed(resp, 'account/authentication/signup_choices.html')
        self.assertTemplateNotUsed(resp, 'account/authentication/signup.html')

    def test_rekisteroitymislomakkeen_avaaminen(self):
        resp = self.client.get('/fi/kayttaja/rekisteroidy/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Salasana')
        self.assertTemplateUsed(resp, 'account/authentication/signup.html')
        self.assertTemplateNotUsed(resp, 'account/authentication/login.html')

    def test_successful_signup(self):
        # Mr. Play-It-Safe
        self.assertEqual(len(mail.outbox), 0)
        reg_data = self.register_user()

        resp = reg_data['response']
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/authentication/signup_activation.html')
        self.assertContains(resp, 'Vahvista rekisteröityminen')

        user = User.objects.get(username='meme')
        self.assertEqual(user.status, User.STATUS_AWAITING_ACTIVATION)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.settings.email, 'me@example.com')
        self.assertEqual(user.settings.first_name, 'Teppo')
        self.assertEqual(user.settings.last_name, 'Testaaja')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        self.assertEqual(mail.outbox[0].recipients()[0], 'me@example.com')
        self.assertEqual(mail.outbox[0].subject, "Vahvista sähköpostiosoitteesi.")
        self.assertFalse('{%' in mail.outbox[0].body)

    def test_missing_fields(self):
        resp = self.client.post('/fi/kayttaja/rekisteroidy/', {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tämä kenttä vaaditaan', 8)

    def test_invalid_username(self):
        resp = self.client.post('/fi/kayttaja/rekisteroidy/',
                                {'user-username': 'meatexample.com'})
        self.assertContains(resp, 'Syötä kelvollinen käyttäjätunnus.', 1)

    def test_email_already_in_use(self):
        UserFactory(settings__email='joku@example.com')
        resp = self.client.post('/fi/kayttaja/rekisteroidy/',
                                {'usersettings-email': 'joku@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/authentication/signup.html')
        self.assertTemplateNotUsed(resp, 'account/authentication/signup_activation.html')
        self.assertContains(resp, 'Sähköpostiosoite on jo käytössä.')


class EmailConfirmation(TestCase):
    def test_vahvista_sahkoposti(self):
        user = UserFactory(status=User.STATUS_AWAITING_ACTIVATION)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(user.is_active)
        token = EmailConfirmationForm.create_token(user)
        resp = self.client.get('/fi/kayttaja/vahvista-sahkoposti/%s/' % token)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/authentication/signup_activated.html')
        self.assertContains(resp, 'Kiitos rekisteröitymisestä')
        self.assertEqual(len(mail.outbox), 1)

    def test_broken_activation_link(self):
        user = UserFactory(is_active=False, status=User.STATUS_AWAITING_ACTIVATION)
        token = EmailConfirmationForm.create_token(user)
        resp = self.client.get('/fi/kayttaja/vahvista-sahkoposti/%s/' % token[1:])
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                'account/authentication/email_confirmation_failed.html')
        self.assertContains(resp, 'Vahvistuslinkki on virheellinen tai vanhentunut.')

    def test_invalid_activation_link(self):
        resp = self.client.get(
            '/fi/kayttaja/vahvista-sahkoposti/abrakadabrsentaytyytoimiamutmitjoseitoimi/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                'account/authentication/email_confirmation_failed.html')
        self.assertContains(resp, 'Vahvistuslinkki on virheellinen tai vanhentunut.')


class LoginTest(TestCase):
    def test_show_login_form(self):
        resp = self.client.get('/fi/kayttaja/kirjaudu-sisaan/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/authentication/login.html')
        self.assertContains(resp, 'Salasana')
        self.assertContains(resp, 'Käyttäjänimi')

    def test_active_user_login(self):
        user = UserFactory(username='Tepotin')
        resp = self.client.post('/fi/kayttaja/kirjaudu-sisaan/', {
            'username': user.username,
            'password': DEFAULT_PASSWORD
        }, follow=True)
        self.assertRedirects(resp, '/fi/kayttaja/{}/'.format(user.pk))
        self.assertContains(resp, 'Tepotin')
        self.assertNotContains(resp, "Ei käyttöoikeutta")

    def test_bad_username(self):
        resp = self.client.post('/fi/kayttaja/kirjaudu-sisaan/', {
            'username': 'ei-ole-tammoista',
            'password': DEFAULT_PASSWORD
        }, follow=True)
        self.assertContains(resp, "Virheellinen käyttäjätunnus tai salasana.",
                            status_code=200)

    def test_inactive_user(self):
        k1 = UserFactory(status=User.STATUS_AWAITING_ACTIVATION)
        k2 = UserFactory(status=User.STATUS_ARCHIVED)
        for user in (k1, k2, ):
            resp = self.client.post('/fi/kayttaja/kirjaudu-sisaan/', {
                'username': user.username,
                'password': DEFAULT_PASSWORD
            }, follow=True)
            self.assertContains(resp, "Käyttäjätunnus ei ole aktiivinen.",
                                status_code=200)

    def test_welcome_messages(self):
        user = UserFactory()
        resp = self.client.post('/fi/kayttaja/kirjaudu-sisaan/', {
            'username': user.username,
            'password': DEFAULT_PASSWORD
        }, follow=True)
        self.assertRedirects(resp, '/fi/kayttaja/%s/' % user.pk, target_status_code=200)
        self.assertNotContains(resp, 'Kirjauduit sisään viimeksi')
        self.assertContains(resp, 'Tervetuloa otakantaa.fi-palveluun!')
        user.joined -= timedelta(minutes=1)
        user.save()
        self.client.logout()
        resp = self.client.post('/fi/kayttaja/kirjaudu-sisaan/', {
            'username': user.username,
            'password': DEFAULT_PASSWORD
        }, follow=True)
        self.assertContains(resp, 'Kirjauduit sisään viimeksi')
        self.assertNotContains(resp, 'Tervetuloa otakantaa.fi palveluun!')


class LogoutTest(TestCase):
    def test_kirjaudu_ulos(self):
        user = UserFactory()
        self.client.login(username=user.username,
                          password=DEFAULT_PASSWORD)
        resp = self.client.get('/fi/kayttaja/kirjaudu-ulos/', follow=True,
                               target_status_code=200)
        self.assertContains(resp, 'Sinut on kirjattu ulos palvelusta')


class CreateSuperuserCommandLineTest(TestCase):
    def test_luo_paakattaja(self):
        self.assertEqual(User.objects.count(), 0)
        call_command('createsuperuser', verbosity=0, interactive=False,
                     username='paakkis123')
        k = User.objects.get(username='paakkis123')
        self.assertTrue(k.is_active)
        self.assertTrue(k.is_superuser)
        self.assertTrue(k.is_staff)


class MyAccountTest(TestCase):
    def setUp(self):
        self.settings = UserSettingsFactory(first_name='Kyösti Kullervo')
        self.user = self.settings.user
        self.client.login(username=self.user.username,
                          password=DEFAULT_PASSWORD)

    def test_user_settings_template(self):
        resp = self.client.get('/fi/kayttaja/{}/asetukset/'.format(self.user.pk))
        self.assertTemplateUsed(resp, 'account/user_settings.html')

    def test_open_edit_user_settings(self):
        resp = self.client.get('/fi/kayttaja/{}/muokkaa-asetukset/'.format(self.user.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/user_settings_edit.html')
        self.assertContains(resp, 'value="Kyösti Kullervo"')

    def test_open_display_user_settings(self):
        resp = self.client.get('/fi/kayttaja/{}/nayta-asetukset/'.format(self.user.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/user_settings_detail.html')
        self.assertContains(resp, '<p>Kyösti Kullervo</p>')

    def test_close_account(self):
        resp = self.client.post('/fi/kayttaja/{}/sulje/'.format(self.user.pk),
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'scheme/schemes.html')
        self.assertContains(resp, 'Käyttäjätili %s suljettu.' % self.user)
        self.assertEqual(len(mail.outbox), 1)


class ProfilePictureTest(TestCase):
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'otakantaa', 'testdata', 'lolcat-sample.jpg')

    def setUp(self):
        self.user = UserSettingsFactory().user
        self.client.login(username=self.user.username,
                          password=DEFAULT_PASSWORD)

    def test_upload_main_pic(self):
        self.assertRaises(ValueError, lambda: self.user.settings.picture.file)
        resp = self.client.post(
            '/fi/kayttaja/%d/asetukset/kuva/muokkaa/' % self.user.pk,
            {'picture': open(self.test_file, 'rb')}
        )
        self.assertEqual(resp.status_code, 232)
        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.picture.url.endswith('.jpg'))
        self.assertTrue(settings.picture_medium.url.endswith('.jpg'))
        self.assertTrue(settings.picture_small.url.endswith('.jpg'))

    def test_open_edit_picture_fragment(self):
        resp = self.client.get('/fi/kayttaja/%d/asetukset/kuva/muokkaa/' % self.user.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/user_settings_base_form.html')
        self.assertTemplateUsed(resp, 'otakantaa/inline_edit_base_form.html')
        self.assertContains(resp, "Uusi kuva")

    def test_open_picture_fragment_no_existing_pic(self):
        resp = self.client.get('/fi/kayttaja/%d/asetukset/kuva/' % self.user.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/user_settings_picture.html')
        self.assertContains(resp, "profile_pic_placeholder")

    def test_open_picture_fragment_with_existing_pic(self):
        self.user.settings.picture.save('lolcat.jpg', File(open(self.test_file, 'rb')))
        resp = self.client.get('/fi/kayttaja/%d/asetukset/kuva/' % self.user.pk)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/user_settings_picture.html')
        self.assertNotContains(resp, "profile_pic_placeholder")
        self.assertContains(resp, '<img')
        self.assertContains(resp, self.user.settings.picture_medium.url)

    def test_delete_picture_fragment_with_existing_pic(self):
        self.user.settings.picture.save('lolcat.jpg', File(open(self.test_file, 'rb')))
        resp = self.client.delete('/fi/kayttaja/%d/asetukset/kuva/poista/' % self.user.pk)
        self.assertEqual(resp.status_code, 232)
        settings = UserSettings.objects.get(pk=self.user.settings.pk)
        self.assertRaises(ValueError, lambda: settings.picture.file)

    def tearDown(self):
        settings = UserSettings.objects.get(user__pk=self.user.pk)
        settings.picture.delete()


class ProfileDetailViewTest(TestCase):
    def setUp(self):
        self.user1 = UserSettingsFactory().user
        self.user2 = UserSettingsFactory().user
        self.moderator = UserFactory(
            groups=[Group.objects.get(name=GROUP_NAME_MODERATORS)]
        )
        self.admin = UserFactory(groups=[Group.objects.get(name=GROUP_NAME_ADMINS)])

    def test_access_user_profile_as_guest(self):
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk), follow=True)
        self.assertRedirects(resp, "/fi/kayttaja/kirjaudu-sisaan/?next=/fi/kayttaja/{}/"
                                   .format(self.user1.pk))
        self.assertContains(resp, "Ei käyttöoikeutta.")
        self.assertContains(resp, "Kirjaudu sisään")

    def test_access_user_profile_as_the_owner(self):
        self.client.login(username=self.user1.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk), follow=True)
        self.assertContains(resp, "Oma sivu")
        self.assertContains(resp, "Omat hankkeet ja osallistumiset")

    def test_access_user_profile_as_another_user(self):
        self.client.login(username=self.user2.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk), follow=True)
        self.assertRedirects(resp, "/fi/kayttaja/kirjaudu-sisaan/")
        self.assertContains(resp, "Ei käyttöoikeutta.")
        self.assertContains(resp, "Kirjaudu sisään")

    def test_access_user_profile_as_moderator(self):
        self.client.login(username=self.moderator.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk), follow=True)
        self.assertContains(resp, "Oma sivu")
        self.assertContains(resp, "Omat hankkeet ja osallistumiset")

    def test_access_user_profile_as_admin(self):
        self.client.login(username=self.admin.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk), follow=True)
        self.assertContains(resp, "Oma sivu")
        self.assertContains(resp, "Omat hankkeet ja osallistumiset")


class ProfileSchemeListTest(TestCase):
    def setUp(self):
        self.user1 = UserSettingsFactory().user
        self.user2 = UserSettingsFactory().user
        self.admin = UserFactory(groups=[
            Group.objects.get(name=GROUP_NAME_ADMINS)
        ])
        self.moderator = UserFactory(groups=[
            Group.objects.get(name=GROUP_NAME_MODERATORS)
        ])
        self.scheme1 = SchemeFactory(owners=[self.user1], title="Public Scheme",
                                     visibility=Scheme.VISIBILITY_PUBLIC)
        SchemeFactory(owners=[self.user1, self.user2], title="Shared Scheme",
                      visibility=Scheme.VISIBILITY_DRAFT)
        SchemeFactory(owners=[self.user1], title="Draft Scheme",
                      visibility=Scheme.VISIBILITY_DRAFT)
        SchemeFactory(owners=[self.user2], title="Non-Owned Scheme",
                      visibility=Scheme.VISIBILITY_DRAFT)

    def test_show_all_schemes_as_owner(self):
        self.client.login(username=self.user1.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/%d/" % self.user1.pk)
        self.assertContains(resp, "Public Scheme", count=1)
        self.assertContains(resp, "Draft Scheme", count=1)
        self.assertContains(resp, "Shared Scheme", count=1)
        self.assertNotContains(resp, "Non-Owned Scheme")

    def test_show_all_schemes_as_admin(self):
        self.client.login(username=self.admin.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/%d/" % self.user1.pk)
        self.assertContains(resp, "Public Scheme", count=1)
        self.assertContains(resp, "Draft Scheme", count=1)
        self.assertContains(resp, "Shared Scheme", count=1)
        self.assertNotContains(resp, "Non-Owned Scheme")

    def test_show_all_schemes_as_moderator(self):
        self.client.login(username=self.moderator.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/%d/" % self.user1.pk)
        self.assertContains(resp, "Public Scheme", count=1)
        self.assertContains(resp, "Draft Scheme", count=1)
        self.assertContains(resp, "Shared Scheme", count=1)
        self.assertNotContains(resp, "Non-Owned Scheme")

    def test_organization_schemes_show_organization_name_as_owner(self):
        organization = OrganizationFactory(admins=[self.user1])
        SchemeOwnersFactory(scheme=SchemeFactory(title="Organization scheme"),
                            organization=organization, user=self.user1)
        self.client.login(username=self.moderator.username, password=DEFAULT_PASSWORD)
        resp = self.client.get("/fi/kayttaja/{}/".format(self.user1.pk))
        self.assertContains(resp, organization.name, 2)
        self.assertContains(resp, "Organization scheme")
