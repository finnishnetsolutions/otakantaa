# coding=utf-8

from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.edit import UpdateView

from libs.ajaxy.responses import AjaxyRedirectResponse

from .responses import AjaxyInlineRedirectResponse, AjaxyReloadResponse, \
    AjaxyBadRequestResponse


class AjaxyFormViewMixIn(object):
    inline_redirect = False

    def form_valid(self, form):
        self.object = form.save()
        return self.get_success_response()

    def get_success_response(self):
        try:
            url = self.get_success_url()
        except ImproperlyConfigured:
            return AjaxyReloadResponse()
        if self.inline_redirect:
            return AjaxyInlineRedirectResponse(url)
        else:
            return AjaxyRedirectResponse(url)

    def form_invalid(self, form):
        resp = super(AjaxyFormViewMixIn, self).form_invalid(form)
        return AjaxyBadRequestResponse(resp.rendered_content)


class AjaxyMultiModelFormViewMixIn(object):
    inline_redirect = False

    def form_valid(self):
        self.save_forms()
        try:
            url = self.get_success_url()
        except (ImproperlyConfigured, AttributeError):
            return AjaxyReloadResponse()
        if self.inline_redirect:
            return AjaxyInlineRedirectResponse(url)
        else:
            return AjaxyRedirectResponse(url)

    def form_invalid(self):
        resp = super(AjaxyMultiModelFormViewMixIn, self).form_invalid()
        return AjaxyBadRequestResponse(resp.rendered_content)


class AjaxyDeleteFormView(AjaxyFormViewMixIn, UpdateView):
    fields = ()
    delete_confirmation = None

    def get_delete_confirmation(self, obj=None):
        return self.delete_confirmation

    def get_context_data(self, **kwargs):
        ctx = super(AjaxyDeleteFormView, self).get_context_data(**kwargs)
        ctx['delete_confirmation'] = self.get_delete_confirmation(obj=ctx['object'])
        return ctx

    def form_valid(self, form):
        self.delete_object(self.get_object())
        return self.get_success_response()

    def get_form_kwargs(self):
        kwargs = super(AjaxyDeleteFormView, self).get_form_kwargs()
        if 'data' not in kwargs and self.request.method in ('POST', 'DELETE', ):
            kwargs['data'] = {}
        return kwargs

    def delete_object(self, obj):
        obj.delete()

    def delete(self, *args, **kwargs):
        return self.post(*args, **kwargs)
