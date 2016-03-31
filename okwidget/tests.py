# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.utils.html import escape
from django.utils.http import urlencode

from content.factories import SchemeFactory, ParticipationDetailsFactory
from content.models import Scheme
from conversation.factories import ConversationFactory, CommentFactory
from conversation.models import Comment


class SchemeListWidgetTest(TestCase):
    def get_next_published(self):
        self.previous_days += 1
        return timezone.now() - timedelta(days=self.previous_days)

    def setUp(self):
        self.previous_days = 30
        self.schemes = [
            SchemeFactory(title={"fi": "Suomiotsikko", "sv": "Svenska schemer"},
                          published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published()),
            SchemeFactory(published=self.get_next_published())
        ]

    def test_widget_modal(self):
        resp = self.client.get("/fi/widget/hankkeet/modal/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "widget/widget_modal.html")
        self.assertTemplateUsed(resp, "widget/widget_content_base.html")
        self.assertTemplateUsed(resp, "widget/scheme_list_widget_content.html")
        self.assertContains(resp, "Widget luodaan käyttämistäsi hakuehdoista.")
        self.assertContains(resp, "Alareunasta löydät iframe-koodin, jonka voit upottaa "
                            "verkkosivuillesi.")
        self.assertContains(resp, "id_limit")
        self.assertContains(resp, "id_language")
        self.assertContains(resp, "Esikatselu")
        self.assertContains(resp, "Koodi")
        self.assertContains(resp,
                            "<iframe src=\"testserver/fi/widget/hankkeet/\"></iframe>")
        self.assertContains(resp, "<main class=\"widget\">", 1)
        self.assertContains(resp, "<div class=\"widget-item\">", 5)
        self.assertContains(resp, self.schemes[0].title)
        self.assertContains(resp, self.schemes[1].title)
        self.assertContains(resp, self.schemes[2].title)
        self.assertContains(resp, self.schemes[3].title)
        self.assertContains(resp, self.schemes[4].title)
        self.assertNotContains(resp, self.schemes[5].title)
        self.assertNotContains(resp, self.schemes[6].title)
        self.assertNotContains(resp, self.schemes[7].title)
        self.assertNotContains(resp, self.schemes[8].title)

    def test_widget_modal_iframe_code(self):
        filters = {"text": self.schemes[1].title,
                   "limit": 4,
                   "status": Scheme.STATUS_CLOSED}
        resp = self.client.get("/fi/widget/hankkeet/modal/", filters)
        iframe = "<iframe src=\"testserver/fi/widget/hankkeet/?{}\"></iframe>"
        query_string = escape(urlencode(filters))
        self.assertContains(resp, iframe.format(query_string))

    def test_widget(self):
        resp = self.client.get("/fi/widget/hankkeet/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "widget/widget.html")
        self.assertTemplateUsed(resp, "widget/widget_content_base.html")
        self.assertTemplateUsed(resp, "widget/scheme_list_widget_content.html")
        self.assertContains(resp, "<main class=\"widget\">", 1)
        self.assertContains(resp, "<div class=\"widget-item\">", 5)
        self.assertContains(resp, self.schemes[0].title)
        self.assertContains(resp, self.schemes[1].title)
        self.assertContains(resp, self.schemes[2].title)
        self.assertContains(resp, self.schemes[3].title)
        self.assertContains(resp, self.schemes[4].title)
        self.assertNotContains(resp, self.schemes[5].title)
        self.assertNotContains(resp, self.schemes[6].title)
        self.assertNotContains(resp, self.schemes[7].title)
        self.assertNotContains(resp, self.schemes[8].title)
        self.assertContains(resp, "Näytä kaikki")

    def test_widget_limit(self):
        resp = self.client.get("/fi/widget/hankkeet/", {"limit": 8})
        self.assertContains(resp, "<div class=\"widget-item\">", 8)
        self.assertContains(resp, self.schemes[0].title)
        self.assertContains(resp, self.schemes[1].title)
        self.assertContains(resp, self.schemes[2].title)
        self.assertContains(resp, self.schemes[3].title)
        self.assertContains(resp, self.schemes[4].title)
        self.assertContains(resp, self.schemes[5].title)
        self.assertContains(resp, self.schemes[6].title)
        self.assertContains(resp, self.schemes[7].title)
        self.assertNotContains(resp, self.schemes[8].title)

    def test_widget_language(self):
        resp = self.client.get("/fi/widget/hankkeet/", {"language": "sv"})
        self.assertNotContains(resp, "Suomiotsikko")
        self.assertContains(resp, "Svenska schemer")

    def test_widget_text_filter(self):
        resp = self.client.get("/fi/widget/hankkeet/", {"text": self.schemes[1].title})
        self.assertNotContains(resp, self.schemes[0].title)
        self.assertContains(resp, self.schemes[1].title)
        self.assertNotContains(resp, self.schemes[2].title)
        self.assertNotContains(resp, self.schemes[3].title)
        self.assertNotContains(resp, self.schemes[4].title)
        self.assertNotContains(resp, self.schemes[5].title)
        self.assertNotContains(resp, self.schemes[6].title)
        self.assertNotContains(resp, self.schemes[7].title)
        self.assertNotContains(resp, self.schemes[8].title)

    # TODO: Test other filters.

    def test_widget_no_results(self):
        Scheme.objects.all().delete()
        resp = self.client.get("/fi/widget/hankkeet/")
        self.assertNotContains(resp, "<div class=\"widget-item\">")
        self.assertContains(resp, "Hankkeita ei löytynyt.")


class SchemeWidgetTest(TestCase):
    def setUp(self):
        self.scheme = SchemeFactory()
        details = [
            ParticipationDetailsFactory(scheme=self.scheme,
                                        content_object=ConversationFactory()),
            ParticipationDetailsFactory(scheme=self.scheme,
                                        content_object=ConversationFactory())
        ]
        self.comments = [
            [CommentFactory(conversation=details[0].content_object),
             CommentFactory(conversation=details[0].content_object),
             CommentFactory(conversation=details[0].content_object)],
            [CommentFactory(conversation=details[1].content_object),
             CommentFactory(conversation=details[1].content_object),
             CommentFactory(conversation=details[1].content_object)]
        ]

    def test_widget_modal(self):
        resp = self.client.get("/fi/widget/hankkeet/{}/modal/".format(self.scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "widget/widget_modal.html")
        self.assertTemplateUsed(resp, "widget/widget_content_base.html")
        self.assertTemplateUsed(resp, "widget/scheme_widget_content.html")
        self.assertContains(resp, "Alareunasta löydät iframe-koodin, jonka voit upottaa "
                            "verkkosivuillesi.")
        self.assertContains(resp, "id_limit")
        self.assertContains(resp, "Esikatselu")
        self.assertContains(resp, "Koodi")
        self.assertContains(
            resp,
            "<iframe src=\"testserver/fi/widget/hankkeet/{}/\"></iframe>"
            .format(self.scheme.pk)
        )
        self.assertContains(resp, "<main class=\"widget\">", 1)
        self.assertContains(resp, "<div class=\"widget-item\">", 5)
        self.assertContains(resp, self.comments[1][2].title)
        self.assertContains(resp, self.comments[1][1].title)
        self.assertContains(resp, self.comments[1][0].title)
        self.assertContains(resp, self.comments[0][2].title)
        self.assertContains(resp, self.comments[0][1].title)
        self.assertNotContains(resp, self.comments[0][0].title)

    def test_widget_modal_iframe_code(self):
        filters = {"limit": 6}
        resp = self.client.get("/fi/widget/hankkeet/{}/modal/".format(self.scheme.pk),
                               filters)
        iframe = "<iframe src=\"testserver/fi/widget/hankkeet/{}/?{}\"></iframe>"
        query_string = escape(urlencode(filters))
        self.assertContains(resp, iframe.format(self.scheme.pk, query_string))

    def test_widget(self):
        resp = self.client.get("/fi/widget/hankkeet/{}/".format(self.scheme.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "widget/widget.html")
        self.assertTemplateUsed(resp, "widget/widget_content_base.html")
        self.assertTemplateUsed(resp, "widget/scheme_widget_content.html")
        self.assertContains(resp, "<main class=\"widget\">", 1)
        self.assertContains(resp, "<div class=\"widget-item\">", 5)
        self.assertContains(resp, self.comments[1][2].title)
        self.assertContains(resp, self.comments[1][1].title)
        self.assertContains(resp, self.comments[1][0].title)
        self.assertContains(resp, self.comments[0][2].title)
        self.assertContains(resp, self.comments[0][1].title)
        self.assertNotContains(resp, self.comments[0][0].title)

    def test_widget_limit(self):
        resp = self.client.get("/fi/widget/hankkeet/{}/".format(self.scheme.pk),
                               {"limit": 3})
        self.assertContains(resp, "<div class=\"widget-item\">", 3)
        self.assertContains(resp, self.comments[1][2].title)
        self.assertContains(resp, self.comments[1][1].title)
        self.assertContains(resp, self.comments[1][0].title)
        self.assertNotContains(resp, self.comments[0][2].title)
        self.assertNotContains(resp, self.comments[0][1].title)
        self.assertNotContains(resp, self.comments[0][0].title)

    def test_widget_no_results(self):
        Comment.objects.all().delete()
        resp = self.client.get("/fi/widget/hankkeet/{}/".format(self.scheme.pk))
        self.assertNotContains(resp, "<div class=\"widget-item\">")
        self.assertContains(resp, "Kommentteja ei löytynyt.")
