# coding=utf-8

from __future__ import unicode_literals

from celery.app import shared_task

from django.core.management import call_command


@shared_task
def archive_idle_schemes():
    call_command("archive_idle_schemes")


@shared_task
def warn_of_archiving():
    call_command("warn_of_archiving")
