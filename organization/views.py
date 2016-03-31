# coding=utf-8

from __future__ import unicode_literals

from datetime import datetime

from django.utils import timezone
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, ugettext
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.views.generic.edit import UpdateView, CreateView

from libs.ajaxy.responses import AjaxyInlineRedirectResponse, AjaxyRedirectResponse

from okmessages.utils import send_message_to_moderators
from organization.forms import CreateOrganizationForm, EditOrganizationPictureForm
from organization.perms import CanEditOrganization
from otakantaa.views import PreFetchedObjectMixIn

from .models import Organization
from .forms import OrganizationSearchFormAdmin, OrganizationSearchForm


class OrganizationListView(ListView):
    paginate_by = 20
    model = Organization
    template_name = 'organization/organization_list.html'
    searchform = None
    form_class = None

    def get_form_kwargs(self):
        return {}

    def get_form_class(self):
        if self.request.user.is_authenticated() and self.request.user.is_moderator:
            return OrganizationSearchFormAdmin
        return OrganizationSearchForm

    def get_queryset(self):
        self.form_class = self.get_form_class()
        self.searchform = self.form_class(
            self.request.GET, **self.get_form_kwargs()
        )
        if self.request.GET and self.searchform.is_valid():
            if self.form_class == OrganizationSearchFormAdmin:
                # todo: moderation
                # qs = Organization.unmoderated_objects.normal_and_inactive()
                qs = Organization.objects.all()
            else:
                qs = Organization.objects.normal()
            return self.searchform.filtrate(qs)
        return Organization.objects.normal().order_by('-created')

    def get_context_data(self, **kwargs):
        kwargs = super(OrganizationListView, self).get_context_data(**kwargs)
        kwargs['searchform'] = self.searchform
        return kwargs


class CreateOrganizationView(CreateView):
    model = Organization
    form_class = CreateOrganizationForm
    template_name = 'organization/create_organization.html'

    def get_initial(self):
        return {'admins': [self.request.user, ]}

    def form_invalid(self, form):
        messages.error(self.request, _("Täytä kaikki pakolliset kentät."))
        return super(CreateOrganizationView, self).form_invalid(form)

    def form_valid(self, form):
        response = super(CreateOrganizationView, self).form_valid(form)
        send_message_to_moderators(
            ugettext("Uusi organisaatio"),
            render_to_string('okmessages/messages/new_organization.txt', {
                'organization': self.object,
                'o_url': self.object.get_absolute_url()
            })
        )
        return response


class OrganizationDetailView(PreFetchedObjectMixIn, DetailView):
    model = Organization

    def get_context_data(self, **kwargs):
        context = super(OrganizationDetailView, self).get_context_data(**kwargs)
        obj = self.get_object()
        context['schemes'] = schemes = obj.owned_schemes.real().schemes()

        # show only public schemes for non admin users
        if not CanEditOrganization(request=self.request,
                                   obj=obj).is_authorized():
            context['schemes'] = schemes.public()
        return context


class OrganizationPartialDetailView(OrganizationDetailView):
    def get_template_names(self):
        return [self.kwargs['template_name'], ]


class OrganizationPartialEditView(PreFetchedObjectMixIn, UpdateView):
    def get_form_class(self):
        return self.kwargs['form_class']

    def get_template_names(self):
        return [
            self.kwargs['template_name'],
            'organization/organization_edit_base_form.html'
        ]

    def form_valid(self, form):
        form.save()
        return AjaxyInlineRedirectResponse(reverse(
            'organization:organization_detail_%s' % self.kwargs['fragment'],
            kwargs={'pk': self.kwargs['pk']}
            ))


class OrganizationSetActiveMixIn(PreFetchedObjectMixIn):
    def get_success_url(self):
        return reverse('organization:detail', kwargs={'pk': self.get_object().pk})

    def set_active(self, active=True):
        obj = self.get_object()
        obj.is_active = active
        if active is True and not obj.activated:
            obj.activated = timezone.now()
        obj.save()


class OrganizationSetActiveView(OrganizationSetActiveMixIn, View):
    active = True

    def post(self, request, **kwargs):
        self.set_active(self.active)
        if self.active:
            messages.success(request, ugettext("Organisaatio on aktivoitu."))
        return AjaxyRedirectResponse(self.get_success_url())


class InlineUpdateView(UpdateView):
    def form_valid(self, form):
        super(InlineUpdateView, self).form_valid(form)
        return AjaxyInlineRedirectResponse(self.get_success_url())


class EditProfilePictureView(PreFetchedObjectMixIn, InlineUpdateView):
    template_name = 'organization/organization_edit_base_form.html'
    form_class = EditOrganizationPictureForm

    def get_success_url(self):
        return reverse('organization:organization_detail_picture',
                       kwargs={'pk': self.get_object().pk})


class ProfilePictureView(PreFetchedObjectMixIn, DetailView):
    template_name = 'organization/organization_detail_picture.html'


class DeleteProfilePictureView(View):
    def delete(self, request, **kwargs):
        obj = get_object_or_404(Organization, pk=kwargs['pk'])
        obj.picture.delete()
        return AjaxyInlineRedirectResponse(reverse(
            'organization:organization_detail_picture',
            kwargs={'pk': obj.pk}))

    def post(self, request, **kwargs):
        return self.delete(request, **kwargs)


class OrganizationTwitterUsernameFormView(UpdateView):
    model = Organization
    fields = ["twitter_username"]
    template_name = "organization/organization_twitter_username_form.html"

    def form_valid(self, form):
        success_msg = "{} {}".format(
            _("Twitter-syötteen käyttäjä vaihdettu."),
            _("Päivittymisessä voi kestää jonkin aikaa.")
        )
        messages.success(self.request, success_msg)
        return super(OrganizationTwitterUsernameFormView, self).form_valid(form)
