# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import patterns, url

from . import views
from .models import Instruction

link_slug_pattern = '{0}|{1}'.format(Instruction.TYPE_PRIVACY_POLICY,
                                     Instruction.TYPE_CONTACT_DETAILS)

urlpatterns = [
    url(r'^$', views.InstructionDetailFirst.as_view(permanent=True), name='instruction_list'),
    url(r'(?P<pk>\d+)/$', views.InstructionDetail.as_view(), name='instruction_detail'),
    url(r'^linkki/(?P<slug>%s)/$' % link_slug_pattern,
        views.LinkedInstructionRedirectView.as_view(permanent=True),
        name='linked_instruction_redirect'),
]
