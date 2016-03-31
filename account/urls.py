# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth import views as auth
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import combo
from libs.djcontrib.views.generic import FlashRedirectView
from libs.permitter.decorators import check_perm
from libs.djcontrib.utils.decorators import obj_by_pk

from otakantaa.decorators import legacy_json_plaintext

from . import views
from .models import User
from .perms import CanEditUser, CanViewUserProfile


urlpatterns = [
    url(r'^rekisteroidy/$', views.SignupView.as_view(), name='signup'),
    url(r'^valitse-rekisteroitymistapa/$', views.SignupChoicesView.as_view(),
        name='signup_choices'),
    url(r'^rekisteroidy/facebook/$', views.SignupView.as_view(facebook=True),
        name='signup_facebook'),
    url(r'^kirjaudu-sisaan/$', views.LoginView.as_view(), name='login'),
    url(r'^kirjaudu-ulos/$', views.LogoutView.as_view(), name='logout'),
    url(r'^aktivoi/$', TemplateView.as_view(
        template_name="account/authentication/signup_activation.html"
    ), name='activate'),
    url(r'^vahvista-sahkoposti/(?P<token>\w{26,50})/$',
        views.EmailConfirmationView.as_view(), name='confirm_email'),
    url(r'^(?P<user_id>\d+)/$',
        obj_by_pk(User, 'user_id')(check_perm(CanViewUserProfile)(
            views.UserProfileView.as_view())), name='profile'),
    url(r'(?P<user_id>\d+)/lista/$', views.UserProfileSchemeListView.as_view(),
        name='scheme_list'),
    url(r'^nollaa-salasana/$', auth.password_reset, name='reset_password',
        kwargs={
            'template_name': 'account/authentication/user_reset_password.html',
            'email_template_name': 'account/email/password_reset.txt',
            'subject_template_name': 'account/email/password_reset_title.txt',
            'post_reset_redirect': 'account:password_reset_done',
        }),
    url(r'^nollaa-salasana/linkki-lahetetty/$', auth.password_reset_done,
        name='password_reset_done',
        kwargs={'template_name':
                'account/authentication/user_reset_password_link_sent.html'}),
    url(r'^nollaa-salasana/vahvista/(?P<uidb64>[0-9A-Za-z_\-]+)'
        '/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth.password_reset_confirm,
        name='password_reset_confirm',
        kwargs={
            'template_name': 'account/authentication/user_reset_password_confirm.html',
            'post_reset_redirect': 'account:password_reset_ready'
        }),
    url(r'^nollaa-salasana/valmis/$',
        FlashRedirectView.as_view(
            message=_("Salasanasi on vaihdettu. Voit nyt kirjautua sisään "
                      "käyttäen uutta salasanaasi."),
            pattern_name='account:login',
            permanent=True
        ), name='password_reset_ready')
]

urlpatterns += decorated_patterns(
    '',
    combo(obj_by_pk(User, 'user_id'), check_perm(CanEditUser)),
    url(r'(?P<user_id>\d+)/asetukset/$', views.UserSettingsView.as_view(),
        name='settings'),
    url(r'(?P<user_id>\d+)/nayta-asetukset/',
        views.UserSettingsDetailView.as_view(),
        name='settings_detail'),
    url(r'(?P<user_id>\d+)/muokkaa-asetukset/',
        views.UserSettingsEditView.as_view(),
        name='settings_edit'),
    url(r'(?P<user_id>\d+)/asetukset/kuva/$', views.ProfilePictureView.as_view(),
        name='profile_picture'),
    url(r'(?P<user_id>\d+)/asetukset/kuva/muokkaa/$',
        legacy_json_plaintext(views.EditProfilePictureView.as_view()),
        name='edit_profile_picture'),
    url(r'(?P<user_id>\d+)/asetukset/kuva/poista/$',
        views.DeleteProfilePictureView.as_view(),
        name='delete_profile_picture'),
    url(r'(?P<user_id>\d+)/sulje/$',
        views.CloseAccountView.as_view(logout=True),
        name='close'),
    url(r'^(?P<user_id>\d+)/salasanan-vaihto/$', views.UserChangePasswordView.as_view(),
        name='password'),
    url(r'^(?P<user_id>\d+)/viestit/$',
        views.MessagesListView.as_view(),
        name="messages"),
    url(r'^(?P<user_id>\d+)/viestit/(?P<message_id>\d+)/$',
        views.MessageDetailView.as_view(),
        name="show_message"),
    url(r'^(?P<user_id>\d+)/viestit/(?P<message_id>\d+)/#(?P<anchor>[-_\w]+)$',
        views.MessageDetailView.as_view(),
        name="show_message"),
    url(r'^(?P<user_id>\d+)/viestit/(?P<message_id>\d+)/vastaa/$',
        views.CreateMessageView.as_view(),
        name="respond_message"),
    url(r'^(?P<user_id>\d+)/viestit/uusi/$',
        views.CreateMessageView.as_view(),
        name="create_message"),
    url(r'^(?P<user_id>\d+)/viestit/uusi/(?P<scheme_id>\d+)/$',
        views.CreateMessageView.as_view(),
        name="create_message"),
    url(r'^(?P<user_id>\d+)/viestit/taulu/$',
        views.MessagesListView.as_view(template_name="account/messages/list_table.html"),
        name="messages_table"),
    url(r'^(?P<user_id>\d+)/viestit/(?P<message_id>\d+)/poista/$',
        views.DeleteMessageView.as_view(),
        name="delete_message"),
    url(r'(?P<user_id>\d+)/muokkaa-ilmoitukset/$',
        views.NotificationOptionsEditView.as_view(),
        name='notification_options_edit'),
    url(r'(?P<user_id>\d+)/nayta-ilmoitukset/$',
        views.NotificationOptionsDetailView.as_view(),
        name='notification_options_detail'),
)
