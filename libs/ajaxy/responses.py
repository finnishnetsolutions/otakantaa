# coding=utf-8

from __future__ import unicode_literals

from django.http.response import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest

from . import statuses


class AjaxyResponseMixIn(object):
    pass


class AjaxyReloadResponse(AjaxyResponseMixIn, HttpResponse):
    status_code = statuses.STATUS_AJAXY_RELOAD


class AjaxyRedirectResponse(AjaxyResponseMixIn, HttpResponseRedirect):
    status_code = statuses.STATUS_AJAXY_REDIRECT


class AjaxyInlineRedirectResponse(AjaxyResponseMixIn, HttpResponseRedirect):
    status_code = statuses.STATUS_AJAXY_INLINE_REDIRECT


class AjaxyBadRequestResponse(AjaxyResponseMixIn, HttpResponseBadRequest):
    pass


class AjaxyNoOperationResponse(AjaxyResponseMixIn, HttpResponse):
    status_code = statuses.STATUS_AJAXY_NO_OPERATION
