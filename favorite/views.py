# coding=utf-8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse

from account.models import User
from favorite.forms import FavoriteTagForm
from libs.ajaxy.responses import AjaxyInlineRedirectResponse
from .models import Favorite


class FavoriteBaseUpdateView(UpdateView):

    def get_object(self):
        return Favorite.objects.filter(user_id=self.request.user.pk,
                                       content_type_id=self.kwargs['content_type_id'],
                                       object_id=self.kwargs['object_id']).first()

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated():
            return False

        if self.get_object():
            self.unfollow()
        else:
            self.follow()
        # TODO: wrong return value !!!
        return True

    def follow(self):
        Favorite.objects.create(
            user_id=self.request.user.pk,
            content_type_id=self.kwargs['content_type_id'],
            object_id=self.kwargs['object_id']
        )

    def unfollow(self):
        obj = self.get_object()
        obj.delete()


class AddOrRemoveSchemeView(FavoriteBaseUpdateView):

    def post(self, request, *args, **kwargs):
        super(AddOrRemoveSchemeView, self).post(request, *args, **kwargs)

        return TemplateResponse(request, 'favorite/follow_link.html',
                                self.get_template_attribute_objects())

    def get_template_attribute_objects(self):
        ct = ContentType.objects.get(pk=self.kwargs['content_type_id'])
        return {
            'obj': ct.get_object_for_this_type(pk=self.kwargs['object_id']),
            'ct': ct,
        }


class UserFavoriteEditView(UpdateView):
    model = User
    pk_url_kwarg = 'user_id'
    template_name = 'favorite/favorite_edit.html'
    form_class = FavoriteTagForm

    def get_form_kwargs(self):
        kwargs = super(UserFavoriteEditView, self).get_form_kwargs()
        ct = ContentType.objects.get_for_id(self.kwargs['ct_id'])
        kwargs['type'] = "{0}.{1}".format(ct.app_label, ct.model)
        return kwargs

    def get_success_url(self):
        return reverse('favorite:favorite_detail', kwargs={
                'user_id': self.kwargs['user_id'],
                'ct_id': self.kwargs['ct_id']
            })

    def form_valid(self, form):
        super(UserFavoriteEditView, self).form_valid(form)
        return AjaxyInlineRedirectResponse(self.get_success_url())


class UserFavoriteDetailView(DetailView):
    template_name = 'favorite/favorite_detail.html'

    def get_object(self):
        return User.objects.get(pk=self.kwargs['user_id'])

    def get_context_data(self, **kwargs):
        context = super(UserFavoriteDetailView, self).get_context_data()
        context['user'] = self.get_object()
        context['ct_id'] = self.kwargs['ct_id']

        ct = ContentType.objects.get_for_id(context['ct_id'])
        if hasattr(ct.model_class(), 'FAVORITE_TEXT'):
            context['title'] = ct.model_class().FAVORITE_TEXT
        else:
            context['title'] = _("Muokkaa")
        return context