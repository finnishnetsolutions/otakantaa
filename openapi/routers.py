# coding=utf-8

from __future__ import unicode_literals

from rest_framework import routers

from . import views


class OpenApiRouter(routers.DefaultRouter):
    pass


router = OpenApiRouter()

router.register('organizations', views.OrganizationViewSet)
router.register('schemes', views.SchemeViewSet)
router.register('tags', views.TagViewSet)
router.register('surveys', views.SurveyViewSet, base_name='survey')
router.register('conversations', views.ConversationViewSet, base_name='conversation')
