# coding=utf-8

from __future__ import unicode_literals

import json

from django.test import TestCase

from content.factories import SchemeFactory


class ApiTestCase(TestCase):
    def get_json(self, *args, **kwargs):
        kwargs.setdefault('HTTP_ACCEPT', 'application/json')
        resp = self.client.get(*args, **kwargs)
        return json.loads(resp.content)

    def assertContainsKeys(self, data, *keys):  # NOQA
        for key in keys:
            self.assertTrue(key in data, "key '%s' missing from data" % key)

    def assertIsPaginated(self, data):  # NOQA
        return self.assertContainsKeys(data, 'results', 'count', 'next', 'previous')


class SchemeApiTest(ApiTestCase):
    def test_list(self):
        scheme = SchemeFactory()
        data = self.get_json('/api/open/0.1/schemes/')
        self.assertIsPaginated(data)
        self.assertEqual(data['results'][0]['title'], scheme.title)

    def test_detail(self):
        scheme = SchemeFactory()
        data = self.get_json('/api/open/0.1/schemes/%d/' % scheme.pk)
        self.assertEqual(data['title'], scheme.title)
        self.assertContainsKeys(data, 'webUrl', 'description', )
