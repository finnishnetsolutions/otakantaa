# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url, include

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import obj_by_pk, combo
from libs.permitter.decorators import check_perm

from otakantaa.decorators import legacy_json_plaintext
from otakantaa.perms import IsAuthenticated

from . import views, forms
from .perms import CanPublishScheme, CanRevertSchemeToDraft, CanAcceptInvitation, \
    CanCloseScheme, CanReopenScheme, CanDeleteScheme, CanViewScheme, CanEditScheme, \
    CanExportSchemePdf, CanExportSchemeExcel, CanExportSchemeWord
from .models import Scheme

scheme_as_obj = obj_by_pk(Scheme, 'scheme_id')
interaction_choices = [str(k) for k, v in Scheme.INTERACTION_CHOICES]

SCHEME_FRAGMENT_URLS = (
    # (url part, template name/url name part, form_class, view_class)
    (r'kuva',           'picture',          forms.EditSchemePictureForm),
    (r'otsikko',        'title',            forms.EditSchemeTitleForm),
    (r'kuvaus',         'description',      forms.EditSchemeDescriptionForm),
    (r'ingressi',       'lead_text',        forms.EditSchemeLeadTextForm),
    (r'yhteenveto',     'summary',          forms.EditSchemeSummaryForm),
    (r'omistajat',      'owners',           None, views.SchemeOwnersEditView),
    (r'aiheet',         'tags',             forms.EditSchemeTagsForm),
    (r'kunnat',         'municipalities',   forms.EditSchemeMunicipalitiesForm),
)

partial_detail_urls = [
    url(r'hankkeet/(?P<scheme_id>\d+)/nayta/%s/$' % u[0],
        views.ContentPartialDetailView.as_view(),
        name='scheme_detail_%s' % u[1],
        kwargs={'template_name': 'content/parts/scheme_detail_%s.html' % u[1]})
    for u in SCHEME_FRAGMENT_URLS
]

partial_edit_patterns = [
    url(r'hankkeet/(?P<scheme_id>\d+)/muokkaa/%s/$' % u[0],
        legacy_json_plaintext((u[3] if len(u) > 3 else
        views.SchemePartialEditView).as_view()), name='edit_scheme_%s' % u[1],
        kwargs={'template_name': 'content/parts/scheme_edit_%s_form.html' % u[1],
                'form_class': u[2], 'fragment': u[1]})
    for u in SCHEME_FRAGMENT_URLS
]

urlpatterns = [
    url(r'hankkeet/uusi/$', check_perm(IsAuthenticated)(views.CreateSchemeView.as_view()),
        name='create_scheme'),
    url(r'hankkeet/(?P<scheme_id>\d+)/julkaise/$',
        scheme_as_obj(check_perm(CanPublishScheme)(views.PublishSchemeView.as_view())),
        name='publish_scheme'),
    url(r'hankkeet/(?P<scheme_id>\d+)/poista/$',
        scheme_as_obj(check_perm(CanDeleteScheme)(views.DeleteSchemeView.as_view())),
        name='delete_scheme'),
    url(r'hankkeet/(?P<scheme_id>\d+)/julkaiseminen/$',
        scheme_as_obj(check_perm(CanPublishScheme)(
            views.TryPublishSchemeView.as_view())), name='try_publish'),
    url(r'hankkeet/(?P<scheme_id>\d+)/paattaminen/$',
        scheme_as_obj(check_perm(CanCloseScheme)(
            views.TryCloseSchemeView.as_view())), name='try_close'),
    url(r'hankkeet/(?P<scheme_id>\d+)/avaa/$',
        scheme_as_obj(check_perm(CanReopenScheme)(views.ReOpenSchemeView.as_view())),
        name='reopen_scheme'),
    url(r'hankkeet/(?P<scheme_id>\d+)/muuta-luonnokseksi/$',
        scheme_as_obj(check_perm(CanRevertSchemeToDraft)(
            views.RevertSchemeToDraftView.as_view())), name='revert_scheme_to_draft'),
    url(r'hankkeet/(?P<scheme_id>\d+)/vahvista-kutsu/(?P<scheme_owner_id>\d+)/',
        scheme_as_obj(check_perm(CanAcceptInvitation)(
            views.SchemeOwnerInvitationView.as_view())), name="owner_invitation"),
    url(r'hankkeet/(?P<scheme_id>\d+)/aseta-osallistujat/(?P<interaction>[' +
        ",".join(interaction_choices) + '])/$',
        scheme_as_obj(check_perm(CanEditScheme)(views.SetInteractionView.as_view())),
        name='scheme_set_interaction'),
    url(r'^rss/$', views.SchemeFeed(), name='rss'),
    url(r'^hankkeet/lataa-lisaa/$', views.LoadSchemesView.as_view(),
        name='load_schemes'),

    # Export.
    url(r'hankkeet/(?P<scheme_id>\d+)/pdf/',
        scheme_as_obj(check_perm(CanExportSchemePdf)(
            views.SchemePdfExportView.as_view()
        )), name="scheme_pdf_export"),
    url(r'hankkeet/(?P<scheme_id>\d+)/excel/',
        scheme_as_obj(check_perm(CanExportSchemeExcel)(
            views.ParticipationExcelExportView.as_view()
        )), name="participation_excel_export"),
    url(r'hankkeet/(?P<scheme_id>\d+)/word/',
        scheme_as_obj(check_perm(CanExportSchemeWord)(
            views.SchemeWordExportView.as_view()
        )), name="participation_word_export"),
]

urlpatterns += decorated_patterns('', scheme_as_obj,
    url(r'hankkeet/(?P<scheme_id>\d+)/osallistuminen/',
        include('content.urls_participation', namespace='participation')),
)

urlpatterns += decorated_patterns('', combo(scheme_as_obj, check_perm(CanViewScheme)),
    url(r'^hankkeet/(?P<scheme_id>\d+)/$', views.SchemeDetailView.as_view(),
        name='scheme_detail'),
    url(r'hankkeet/(?P<scheme_id>\d+)/liitteet/nayta/$', views.AttachmentsDetailView.
        as_view(), name='attachment_list'),
    *partial_detail_urls
)

urlpatterns += decorated_patterns('', combo(scheme_as_obj, check_perm(CanEditScheme)),
    url(r'hankkeet/(?P<scheme_id>\d+)/poista/kuva/$',
        views.DeleteSchemePictureView.as_view(), name='delete_scheme_picture'),
    url(r'hankkeet/(?P<scheme_id>\d+)/liitteet/muokkaa/$',
        views.UploadMultipleAttachmentsSchemeView.as_view(), name='add_attachments'),
    url(r'hankkeet/(?P<scheme_id>\d+)/liitteet/(?P<upload_id>\d+)/poista/$',
        views.DeleteAttachmentView.as_view(), name='delete_attachment'),
    url(r'hankkeet/(?P<scheme_id>\d+)/esimoderointi/(?P<premoderation_state>(0|1))/$',
        views.PremoderationToggleView.as_view(), name='toggle_premoderation'),
    url(r'^hankkeet/(?P<scheme_id>\d+)/twitter-hakusana/$',
        views.SchemeTwitterSearchFormView.as_view(), name="twitter_search"),
    *partial_edit_patterns
)
