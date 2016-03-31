# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import combo, obj_by_pk
from libs.permitter.decorators import check_perm

from organization.perms import CanActivateOrganization
from otakantaa.decorators import legacy_json_plaintext
from otakantaa.perms import IsAuthenticated

from . import views, forms
from .models import Organization
from .perms import CanViewOrganization, CanEditOrganization

org_by_pk = obj_by_pk(Organization, 'pk')

# TODO: DRY against content.urls, generic edit&detail view?

ORGANIZATION_FRAGMENT_URLS = (
    # (url part, template name/url name part, form_class)
    (r'kuva',           'picture',          forms.EditOrganizationPictureForm),
    (r'kuvaus',         'description',      forms.EditOrganizationDescriptionForm),
    (r'yhteyshenkilot', 'admins',           forms.EditOrganizationAdminsForm),
    (r'nimi',           'name',             forms.EditOrganizationNameForm),
    (r'tyyppi',         'type',             forms.EditOrganizationTypeForm),
)

partial_detail_urls = [
    url(r'(?P<pk>\d+)/nayta/%s/$' % u[0],
        views.OrganizationPartialDetailView.as_view(),
        name='organization_detail_%s' % u[1],
        kwargs={'template_name': 'organization/organization_detail_%s.html' % u[1]}
    ) for u in ORGANIZATION_FRAGMENT_URLS
]

partial_edit_patterns = [
    url(r'(?P<pk>\d+)/muokkaa/%s/$' % u[0],
        legacy_json_plaintext(views.OrganizationPartialEditView.as_view()),
        name='edit_organization_%s' % u[1],
        kwargs={'template_name': 'organization/organization_edit_%s_form.html' % u[1],
                'form_class': u[2], 'fragment': u[1]}
    ) for u in ORGANIZATION_FRAGMENT_URLS
]


urlpatterns = [
    url(r'^$', views.OrganizationListView.as_view(), name='list'),
    url(r'uusi/$', check_perm(IsAuthenticated)(views.CreateOrganizationView.as_view()),
        name='create'),
    url(r'^(?P<pk>\d+)/piilota/', org_by_pk(check_perm(CanEditOrganization)(
            views.OrganizationSetActiveView.as_view(active=False))), name='deactivate'),
    url(r'^(?P<pk>\d+)/aktivoi/', org_by_pk(check_perm(CanActivateOrganization)(
        views.OrganizationSetActiveView.as_view(active=True))), name='activate'),
]

urlpatterns += decorated_patterns('', combo(org_by_pk, check_perm(CanViewOrganization)),
    url(r'(?P<pk>\d+)/$', views.OrganizationDetailView.as_view(), name='detail'),
    *partial_detail_urls
) + decorated_patterns('', combo(org_by_pk, check_perm(CanEditOrganization)),
    url(r'(?P<pk>\d+)/kuva/muokkaa/$',
        views.EditProfilePictureView.as_view(),
        name='edit_picture'),
    url(r'(?P<pk>\d+)/kuva/poista/$',
        views.DeleteProfilePictureView.as_view(),
        name='delete_picture'),
    url(r'^(?P<pk>\d+)/twitter-kayttajanimi/$',
        views.OrganizationTwitterUsernameFormView.as_view(),
        name="twitter_username_form"),
    *partial_edit_patterns
)
