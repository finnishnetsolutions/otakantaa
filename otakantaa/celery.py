# coding=utf-8

from __future__ import absolute_import, unicode_literals

from celery import Celery

from django.conf import settings


app = Celery('otakantaa')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

