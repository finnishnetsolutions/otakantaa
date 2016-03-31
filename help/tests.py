# coding=utf-8

from __future__ import unicode_literals

from django.test import TestCase

from .factories import InstructionFactory
from .models import Instruction


class HelpTest(TestCase):
    def test_open_instruction_list_without_instructions(self):
        resp = self.client.get("/fi/tietoa-palvelusta/")
        self.assertEqual(resp.status_code, 404)

    def test_open_instruction_list_with_instructions(self):
        instruction_1 = InstructionFactory(description="Sleep well.")
        instruction_2 = InstructionFactory(description="Don't eat too much.")
        resp = self.client.get("/fi/tietoa-palvelusta/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertRedirects(resp, "/fi/tietoa-palvelusta/{}/".format(instruction_1.pk),
                             status_code=301)
        self.assertTemplateUsed(resp, "help/instruction_list.html")
        self.assertTemplateUsed(resp, "help/instruction_detail.html")
        self.assertContains(resp, "Tietoa palvelusta")
        self.assertContains(resp, instruction_1.title)
        self.assertContains(resp, instruction_2.title)
        self.assertContains(resp, instruction_1.description)
        self.assertNotContains(resp, instruction_2.description)

    def test_open_privacy_policies(self):
        instruction = InstructionFactory(
            connect_link_type=Instruction.TYPE_PRIVACY_POLICY
        )
        resp = self.client.get("/fi/tietoa-palvelusta/linkki/privacy-policy/",
                               follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertRedirects(resp, "/fi/tietoa-palvelusta/{}/".format(instruction.pk),
                             status_code=301)
        self.assertContains(resp, instruction.title)
        self.assertContains(resp, instruction.description)

    def test_open_contact_details(self):
        instruction = InstructionFactory(
            connect_link_type=Instruction.TYPE_CONTACT_DETAILS
        )
        resp = self.client.get("/fi/tietoa-palvelusta/linkki/contact-details/",
                               follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertRedirects(resp, "/fi/tietoa-palvelusta/{}/".format(instruction.pk),
                             status_code=301)
        self.assertContains(resp, instruction.title)
        self.assertContains(resp, instruction.description)
