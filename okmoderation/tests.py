# coding=utf-8

from django.contrib.contenttypes.models import ContentType

import json

from otakantaa.test.testcases import TestCase
from okmoderation.models import ContentFlag
from content.factories import SchemeFactory
from content.models import Scheme

from libs.moderation.models import ModeratedObject, MODERATION_STATUS_PENDING


class FlaggingTest(TestCase):
    def test_flag_form(self):
        scheme = SchemeFactory()
        ct = ContentType.objects.get_for_model(Scheme)
        resp = self.client.get('/fi/ilmoita-asiaton-sisalto/%d/%d/' % (ct.pk, scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'okmoderation/flag_content_form.html')
        self.assertContains(resp, 'Syy')

    def test_flag_scheme(self):
        scheme = SchemeFactory()
        ct = ContentType.objects.get_for_model(Scheme)

        self.assertEqual(ModeratedObject.objects.filter(
            moderation_status=MODERATION_STATUS_PENDING
        ).count(), 0)

        self.assertEqual(ContentFlag.objects.count(), 0)
        resp = self.client.post(
            '/fi/ilmoita-asiaton-sisalto/%d/%d/' % (ct.pk, scheme.pk), {
                'reason': 'i dont like it, put it away'})

        self.assertEqual(resp.status_code, 205)
        self.assertEqual(ContentFlag.objects.count(), 1)
        flag = ContentFlag.objects.first()
        self.assertEqual(flag.content_object, scheme)
        self.assertEqual(ModeratedObject.objects.filter(
            moderation_status=MODERATION_STATUS_PENDING
        ).count(), 1)
