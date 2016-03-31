# coding=utf-8

from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.views.generic.base import RedirectView

from content.views import UploadAttachmentView, SchemesView

from libs.djcontrib.utils.decorators import combo
from libs.permitter.decorators import check_perm
from libs.moderation.helpers import auto_discover

from okmessages.views import FeedbackView

from .views import AllowedFileUploadExtensions, error_page_not_found
from .decorators import legacy_json_plaintext
from .perms import IsAuthenticated


auto_discover()

urlpatterns = [
    url('^api/$', RedirectView.as_view(url='/api/open/0.1/', permanent=False)),  # HACK
    url(r'^api/open/', include('openapi.urls', namespace='openapi')),
]

urlpatterns += i18n_patterns(
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', SchemesView.as_view(), name='schemes'),
    url(r'^kayttaja/', include('account.urls', namespace='account')),
    url(r'^', include('content.urls', namespace='content')),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^hallinta/', include('okadmin.urls', namespace='okadmin')),
    url('^liitteet/laheta/(?P<upload_group_id>[a-f0-9]{32})'
        '(?P<upload_token>[a-f0-9]{32})/$',
        combo(check_perm(IsAuthenticated), legacy_json_plaintext)(
            UploadAttachmentView.as_view()
        ),
        name='attachtor_file_upload'),
    url('^liitteet/sallitut-paatteet/$', AllowedFileUploadExtensions.as_view(),
        name='allowed_file_upload_extensions'),
    url(r'^redactor/', include('redactor.urls')),
    url(r'^', include('survey.urls', namespace='survey')),
    url(r'keskustelut/', include('conversation.urls', namespace='conversation')),
    url(r'^suosikit/', include('favorite.urls', namespace='favorite')),
    url(r'^organisaatiot/', include('organization.urls', namespace='organization')),
    url(r'^palaute/$', FeedbackView.as_view(), name='feedback'),
    url(r'', include('okmoderation.urls', namespace='okmoderation')),
    url(r'^widget/', include('okwidget.urls', namespace='widget')),
    url(r'^tietoa-palvelusta/', include('help.urls', namespace='help')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.STATIC_URL.startswith('http'):
    urlpatterns += staticfiles_urlpatterns('/static/')

handler404 = error_page_not_found
