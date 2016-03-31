# conding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.conf import settings
from ...utils import warn_of_archiving


class Command(BaseCommand):
    def handle(self, *args, **options):
        warn_days = settings.AUTO_ARCHIVE_DAYS - settings.AUTO_ARCHIVE_WARNING_DAYS
        warn_date = date.today() - timedelta(days=warn_days)
        archive_date = date.today() - timedelta(days=settings.AUTO_ARCHIVE_DAYS)
        warn_of_archiving(warn_date, archive_date)
