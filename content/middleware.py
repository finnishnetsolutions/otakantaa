# coding=utf-8

from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.utils.functional import SimpleLazyObject
from django.contrib.contenttypes.models import ContentType
from content.models import ParticipationDetails


class RequestParticipationMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'participation_detail_id' in view_kwargs:
            request.participation_detail = SimpleLazyObject(
                lambda: get_object_or_404(ParticipationDetails,
                                          pk=view_kwargs['participation_detail_id'])
            )
        else:
            keys = {'conversation_id': 'conversation', 'survey_id': 'survey'}
            for k, v in keys.iteritems():
                if k in view_kwargs:
                    ct = ContentType.objects.get_by_natural_key(v, v)
                    request.participation_detail = SimpleLazyObject(
                        lambda: get_object_or_404(ParticipationDetails, content_type=ct,
                                                  object_id=view_kwargs[k]))
                    break

    def process_response(self, request, response):
        if hasattr(request, 'participation_detail'):
            del request.participation_detail
        return response
