# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^hankkeet/$', views.SchemeListWidgetView.as_view(),
        name="scheme_list"),
    url(r'^hankkeet/modal/$', views.SchemeListWidgetModalView.as_view(),
        name="scheme_list_modal"),
    url(r'^hankkeet/(?P<scheme_id>\d+)/$',
        views.SchemeWidgetView.as_view(), name="scheme"),
    url(r'^hankkeet/(?P<scheme_id>\d+)/modal/$',
        views.SchemeWidgetModalView.as_view(), name="scheme_modal"),
]
