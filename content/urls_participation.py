# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url, include

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import obj_by_pk, combo
from libs.permitter.decorators import check_perm

from otakantaa.decorators import legacy_json_plaintext

from . import views, forms
from .models import Scheme, ParticipationDetails
from .perms import CanEditScheme, CanViewParticipation, CanEditParticipation, \
    CanDeleteParticipation, CanPublishParticipation


scheme_as_obj = obj_by_pk(Scheme, 'scheme_id')
participation_as_obj = obj_by_pk(ParticipationDetails, 'participation_detail_id')

PARTICIPATION_FRAGMENT_URLS = (
    (r'otsikko',         'title',           forms.EditParticipationTitleForm),
    (r'kuvaus',          'description',     forms.EditParticipationDescriptionForm),
    (r'paattymispaiva', 'expiration_date',  forms.EditParticipationExpirationDateForm,
     views.ParticipationExpirationDateEditView),
)

partial_detail_urls = [
    url(r'(?P<participation_detail_id>\d+)/nayta/%s/$' % u[0],
        views.ParticipationPartialDetailView.as_view(),
        name='participation_detail_%s' % u[1],
        kwargs={'template_name': 'content/parts/participation_detail_%s.html' % u[1]})
    for u in PARTICIPATION_FRAGMENT_URLS
]

partial_edit_patterns = [
    url(r'(?P<participation_detail_id>\d+)/muokkaa/%s/$' % u[0],
        legacy_json_plaintext((u[3] if len(u) > 3 else
                               views.ParticipationPartialEditView).as_view()),
        name='edit_participation_%s' % u[1],
        kwargs={'template_name': 'content/parts/participation_edit_%s_form.html' % u[1],
                'form_class': u[2], 'fragment': u[1]})
    for u in PARTICIPATION_FRAGMENT_URLS
]

urlpatterns = [
    url(r'(?P<participation_detail_id>\d+)/liitteet/muokkaa/$',
        participation_as_obj(check_perm(CanEditParticipation)(
            views.UploadMultipleAttachmentsParticipationView.as_view())),
        name='add_attachments'),
    url(r'(?P<participation_detail_id>\d+)/poista/$',
        participation_as_obj(check_perm(CanDeleteParticipation)(
            views.DeleteParticipationDetailView.as_view())),
        name='delete_participation'),
]

urlpatterns += decorated_patterns('', combo(participation_as_obj,
                                            check_perm(CanViewParticipation)),
    url(r'(?P<participation_detail_id>\d+)/keskustelu/$', views.ConversationDetailView.
        as_view(), name='conversation_detail'),
    url(r"(?P<participation_detail_id>\d+)/kysely/$", views.SurveyDetailView.as_view(),
        name="survey_detail"),
    url(r'(?P<participation_detail_id>\d+)/liitteet/nayta/$',
        views.AttachmentsDetailView.as_view(), name='attachment_list'),
    *partial_detail_urls
)

urlpatterns += decorated_patterns('', combo(scheme_as_obj, check_perm(CanEditScheme)),
    url(r'keskustelu/uusi/$', views.CreateConversationView.as_view(),
        name='create_conversation'),
    url(r'(?P<participation_detail_id>\d+)/vaihda-tila/', include([
        url(r'avaa/$', participation_as_obj(check_perm(CanPublishParticipation)(
            views.OpenParticipationView.as_view())), name='open_participation'),
        url(r'sulje/$', views.EndParticipationView.as_view(), name='close_participation'),
    ])),
    url(r'kysely/uusi/$', views.CreateSurveyView. as_view(), name='create_survey'),
    url(r"(?P<participation_detail_id>\d+)/kysely/muokkaa/$",
        views.SurveyDetailView.as_view(edit_mode=True), name="survey_edit"),
    url(r"(?P<participation_detail_id>\d+)/kysely/tulosten_naytto/(?P<value>\d+)/$",
        views.UpdateSurveyShowResults.as_view(), name="survey_set_show_results"),
    *partial_edit_patterns
)
