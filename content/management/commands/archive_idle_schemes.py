# conding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.conf import settings
from ...utils import archive_idle_schemes


class Command(BaseCommand):
    def handle(self, *args, **options):
        reference_day = date.today() - timedelta(days=settings.AUTO_ARCHIVE_DAYS)
        archive_idle_schemes(reference_day)
