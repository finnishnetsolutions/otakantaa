from django.test import TestCase
from django.conf import settings
from actions.models import SentEmails
from .tasks import create_weekly_notifications

settings.TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'


class CeleryTest(TestCase):
    def test_weekly_notifications(self):
        pass