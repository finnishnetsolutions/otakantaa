# coding=utf-8

from __future__ import unicode_literals

from django.http.response import HttpResponse, Http404
from django.shortcuts import render
from django.views.generic.base import View
from django.conf import settings


class AllowedFileUploadExtensions(View):
    def get(self, request, **kwargs):
        return HttpResponse("\n".join(sorted(settings.FILE_UPLOAD_ALLOWED_EXTENSIONS)),
                            content_type='text/plain')


class PreFetchedObjectMixIn(object):
    obj_kwarg = 'obj'

    def get_object(self):
        return self.kwargs[self.obj_kwarg]


def error_page_not_found(request):
    return render(request, 'otakantaa/404.html', status=404)
