# coding=utf-8

from __future__ import unicode_literals

import datetime

from datetime import date

from unittest.case import skipUnless

from django.conf import settings
from django.template.base import Template
from django.template.context import Context
from django.test.testcases import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.encoding import force_text

from .forms import BasicContactForm, BasicUserForm, ContactModelForm, UserModelForm
from libs.formidable.tests.forms import UserModelFormWithBasicProfileForm
from .models import Contact, ContactPhone, User, Profile


@override_settings(LANGUAGE_CODE='en')
class BasicFormInlineFormSetTest(TestCase):
    def assert_form_valid(self, form):
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        cleaned = form.cleaned_data
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(cleaned['phones']), 2)
        self.assertEqual(len(cleaned['phones'][0]), 2)
        self.assertEqual(len(cleaned['phones'][1]), 2)
        self.assertEqual(cleaned['name'], 'dan man')
        self.assertEqual(cleaned['phones'][0]['number'], '12345678')
        self.assertEqual(force_text(cleaned['phones'][0]['type']),
                         force_text(ContactPhone.TYPE_LANDLINE))
        self.assertEqual(cleaned['phones'][1]['number'], '132212')
        self.assertEqual(force_text(cleaned['phones'][1]['type']),
                         force_text(ContactPhone.TYPE_MOBILE))

    def test_render_empty_form(self):
        form = BasicContactForm()
        html = force_text(form)
        self.assertEqual(html.count(' name="phones-0-type"'), 1)

    def test_initial(self):
        form = BasicContactForm(
            initial={
                'name': 'Jimmy',
                'phones': [{'number': '12345678'},
                           {'number': '23456789', 'type': 'BUH'}]}
        )
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="name"[^\>]+value="Jimmy"')
        self.assertRegexpMatches(html, 'name="phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html, 'name="phones-1-number"[^\>]+value="23456789"')
        self.assertFalse('Select a valid choice.' in html)

    def test_initial_with_prefix(self):
        form = BasicContactForm(
            initial={
                'name': 'Jimmy',
                'phones': [{'number': '12345678', 'type': 'DOH'},
                           {'number': '23456789'}]},
            prefix='contact'
        )
        html = force_text(form)
        self.assertRegexpMatches(html,
                                 'name="contact-name"[^\>]+value="Jimmy"')
        self.assertRegexpMatches(html,
                                 'name="contact-phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html,
                                 'name="contact-phones-1-number"[^\>]+value="23456789"')
        self.assertFalse('Select a valid choice.' in html)

    def test_validate_failure(self):
        form = BasicContactForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': 'DOH',
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertFalse('name' in form.errors)
        self.assertEqual(form.cleaned_data['name'], 'dan man')
        self.assertTrue('phones' in form.errors)
        self.assertFalse('phones' in form.cleaned_data)
        self.assertEqual(len(form.errors['phones']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="name"[^\>]+value="dan man"')
        self.assertRegexpMatches(html, 'name="phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html, 'name="phones-1-number"[^\>]+value="132212"')
        self.assertTrue('Select a valid choice. DOH is not one of the available '
                        'choices.' in html)

    def test_validate_failure_with_prefix(self):
        form = BasicContactForm(
            data={
                'contact-name': 'dan man',
                'contact-phones-0-number': '12345678',
                'contact-phones-0-type': 'DOH',
                'contact-phones-1-number': '132212',
                'contact-phones-1-type': ContactPhone.TYPE_MOBILE,
            },
            prefix='contact'
        )
        self.assertFalse(form.is_valid())
        self.assertFalse('name' in form.errors)
        self.assertEqual(form.cleaned_data['name'], 'dan man')
        self.assertTrue('phones' in form.errors)
        self.assertFalse('phones' in form.cleaned_data)
        self.assertEqual(len(form.errors['phones']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html,
                                 'name="contact-name"[^\>]+value="dan man"')
        self.assertRegexpMatches(html,
                                 'name="contact-phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html,
                                 'name="contact-phones-1-number"[^\>]+value="132212"')
        self.assertTrue('Select a valid choice. DOH is not one of the available '
                        'choices.' in html)

    def test_validate_success(self):
        form = BasicContactForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
            }
        )
        self.assert_form_valid(form)

    def test_validate_success_with_prefix(self):
        form = BasicContactForm(
            data={
                'contact-name': 'dan man',
                'contact-phones-0-number': '12345678',
                'contact-phones-0-type': ContactPhone.TYPE_LANDLINE,
                'contact-phones-1-number': '132212',
                'contact-phones-1-type': ContactPhone.TYPE_MOBILE,
            },
            prefix='contact'
        )
        self.assert_form_valid(form)

    def test_manual_forms_rendering(self):
        form = BasicContactForm(
            data={
                'contact-name': 'dan man',
                'contact-phones-0-number': '12345678',
                'contact-phones-0-type': ContactPhone.TYPE_LANDLINE,
                'contact-phones-1-number': '132212',
                'contact-phones-1-type': ContactPhone.TYPE_MOBILE,
            },
            prefix='contact'
        )
        template = """
        {% for subform in form.phones %}
            <!-- subform start -->
            {% for field in subform %}
                <!-- subfield start -->
                {{ field }}
            {% endfor %}
        {% endfor %}
        """
        html = Template(template).render(Context({'form': form}))
        self.assertFalse('class="formidable-formset"' in html)
        self.assertFalse('<script' in html)
        self.assertEqual(html.count('<!-- subform start -->'), 2)
        self.assertEqual(html.count('<!-- subfield start -->'), 4)
        self.assertEqual(html.count('name="contact-phones-'), 4)
        self.assertEqual(html.count('name="contact-phones-0'), 2)
        self.assertEqual(html.count('name="contact-phones-1'), 2)

    def test_empty_form_deletable_and_updatable(self):
        form = BasicContactForm()
        html = force_text(form)
        self.assertEqual(html.count('data-deletable=\\"1\\"'), 1)
        self.assertEqual(html.count('data-updatable=\\"1\\"'), 1)

    def test_delete_button_type_button(self):
        form = BasicContactForm()
        html = force_text(form)
        self.assertEqual(
            html.count('\\u003cbutton type=\\"button\\" '
                       'class=\\"formidable-formset-form-delete'),
            1
        )


@override_settings(LANGUAGE_CODE='en')
class BasicFormInlineFormTest(TestCase):
    def assert_form_valid(self, form):
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        cleaned = form.cleaned_data
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(cleaned['profile']), 3)
        self.assertEqual(cleaned['username'], 'puppet')
        self.assertEqual(cleaned['profile']['first_name'], 'Mr.')
        self.assertEqual(cleaned['profile']['last_name'], 'Puppet')
        self.assertEqual(cleaned['profile']['dob'], date(1969, 6, 9))

    def test_render_empty_form(self):
        form = BasicUserForm()
        html = force_text(form)
        self.assertEqual(html.count(' name="profile-dob"'), 1)

    def test_initial(self):
        form = BasicUserForm(
            initial={
                'username': 'puppet',
                'profile': {'first_name': 'Mr.', 'last_name': 'Puppet',
                            'dob': date(1969, 6, 9)}
            }
        )
        html = force_text(form)
        self.assertFalse('&#39;' in html)  # widget attrs escaping fail
        self.assertRegexpMatches(html, 'name="username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html, 'name="profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="profile-last_name"[^\>]+value="Puppet"')
        self.assertRegexpMatches(html, 'name="profile-dob"[^\>]+value="1969-06-09"')
        self.assertFalse('error' in html)


    def test_initial_with_prefix(self):
        form = BasicUserForm(
            initial={
                'username': 'puppet',
                'profile': {'first_name': 'Mr.', 'last_name': 'Puppet',
                            'dob': date(1969, 6, 9)}
            },
            prefix='user'
        )
        html = force_text(form)
        self.assertRegexpMatches(html,
                                 'name="user-username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html,
                                 'name="user-profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html,
                                 'name="user-profile-last_name"[^\>]+value="Puppet"')
        self.assertRegexpMatches(html,
                                 'name="user-profile-dob"[^\>]+value="1969-06-09"')
        self.assertFalse('error' in html)

    def test_validate_failure(self):
        form = BasicUserForm(
            data={
                'username': 'puppet',
                'profile-first_name': 'Mr.',
                'profile-last_name': 'Puppet',
                'profile-dob': '12341',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertFalse('username' in form.errors)
        self.assertEqual(form.cleaned_data['username'], 'puppet')
        self.assertTrue('profile' in form.errors)
        self.assertFalse('profile' in form.cleaned_data)
        self.assertEqual(len(form.errors['profile']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html, 'name="profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="profile-last_name"[^\>]+value="Puppet"')
        self.assertTrue('Enter a valid date' in html)

    def test_validate_failure_with_prefix(self):
        form = BasicUserForm(
            data={
                'user-username': 'puppet',
                'user-profile-first_name': 'Mr.',
                'user-profile-last_name': 'Puppet',
                'user-profile-dob': '132212'
            },
            prefix='user'
        )
        self.assertFalse(form.is_valid())
        self.assertFalse('username' in form.errors)
        self.assertEqual(form.cleaned_data['username'], 'puppet')
        self.assertTrue('profile' in form.errors)
        self.assertFalse('profile' in form.cleaned_data)
        self.assertEqual(len(form.errors['profile']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="user-username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html, 'name="user-profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="user-profile-last_name"[^\>]+value="Puppet"')
        self.assertTrue('Enter a valid date' in html)

    def test_validate_success(self):
        form = BasicUserForm(
            data={
                'username': 'puppet',
                'profile-first_name': 'Mr.',
                'profile-last_name': 'Puppet',
                'profile-dob': '1969-06-09',
                #'profile-mmn': 'Doe'  # extra field, must not exist in cleaned_data
            }
        )
        self.assert_form_valid(form)

    def test_validate_success_with_prefix(self):
        form = BasicUserForm(
            data={
                'user-username': 'puppet',
                'user-profile-first_name': 'Mr.',
                'user-profile-last_name': 'Puppet',
                'user-profile-dob': '1969-06-09'
            },
            prefix='user'
        )
        self.assert_form_valid(form)

    def test_manual_subform_fields_rendering(self):
        form = BasicUserForm(
            data={
                'user-username': 'puppet',
                'user-profile-first_name': 'Mr.',
                'user-profile-last_name': 'Puppet',
                'user-profile-dob': '1969-06-09',
            },
            prefix='user'
        )
        template = """
        <!-- subform start -->
        {% for field in form.profile %}
            <!-- subfield start -->
            {{ field }}
        {% endfor %}
        """
        html = Template(template).render(Context({'form': form}))
        self.assertFalse('class="formidable-formset"' in html)
        self.assertFalse('<script' in html)
        self.assertEqual(html.count('<!-- subfield start -->'), 3)
        self.assertEqual(html.count('name="user-profile-'), 3)
        self.assertEqual(html.count('name="user-profile-first_name'), 1)
        self.assertEqual(html.count('name="user-profile-last_name'), 1)
        self.assertEqual(html.count('name="user-profile-dob'), 1)


@override_settings(LANGUAGE_CODE='en')
class ModelFormInlineFormSetTest(TestCase):
    multi_db = True

    def assert_form_valid(self, form):
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        cleaned = form.cleaned_data
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(cleaned['phones']), 2)
        self.assertEqual(len(cleaned['phones'][0]), 3)
        self.assertEqual(len(cleaned['phones'][1]), 3)
        self.assertEqual(cleaned['name'], 'dan man')
        self.assertEqual(cleaned['phones'][0]['number'], '12345678')
        self.assertEqual(cleaned['phones'][0]['type'],
                         ContactPhone.TYPE_LANDLINE)
        self.assertEqual(cleaned['phones'][1]['number'], '132212')
        self.assertEqual(cleaned['phones'][1]['type'],
                         ContactPhone.TYPE_MOBILE)

    def test_render_empty_form(self):
        form = ContactModelForm()
        html = force_text(form)
        self.assertEqual(html.count(' name="phones-0-type"'), 1)

    def test_initial_from_instance(self):
        contact = Contact.objects.create(name='babar')
        phone1 = contact.phones.create(number='12345678', type=ContactPhone.TYPE_MOBILE)
        phone2 = contact.phones.create(number='23456789', type=ContactPhone.TYPE_MOBILE,
                                       delete_lock=True)
        form = ContactModelForm(instance=contact)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="name"[^\>]+value="babar"')
        self.assertRegexpMatches(html, 'name="phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html, 'name="phones-0-id"[^\>]+value="{}"'.format(
            phone1.pk
        ))
        self.assertRegexpMatches(html, 'name="phones-1-number"[^\>]+value="23456789"')
        self.assertRegexpMatches(html, 'name="phones-1-id"[^\>]+value="{}"'.format(
            phone2.pk
        ))
        self.assertEqual(html.count('data-object-id="{}"'.format(phone1.pk)), 1)
        self.assertEqual(html.count('data-object-id="{}"'.format(phone2.pk)), 1)

        self.assertEqual(html.count('data-deletable="1"'), 1)
        self.assertEqual(html.count('data-deletable="0"'), 1)
        self.assertEqual(html.count('data-updatable="1"'), 2)
        self.assertEqual(html.count('selected="selected">Mobile</option>'), 2)
        self.assertFalse('Select a valid choice.' in html)

    def test_initial_after_failed_validation(self):
        contact = Contact.objects.create(name='babar')
        phone1 = contact.phones.create(number='12345678', type=ContactPhone.TYPE_MOBILE,
                                       update_lock=True)
        phone2 = contact.phones.create(number='23456789', type=ContactPhone.TYPE_MOBILE,
                                       delete_lock=True, update_lock=True)
        form = ContactModelForm(
            data={
                'name': '',
                'phones-0-number': phone1.number,
                'phones-0-type': phone1.type,
                'phones-0-id': phone1.pk,
                'phones-4-number': phone2.number,
                'phones-4-type': phone2.type,
                'phones-4-id': phone2.pk,
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html, 'name="phones-0-id"[^\>]+value="{}"'.format(
            phone1.pk
        ))
        self.assertRegexpMatches(html, 'name="phones-1-number"[^\>]+value="23456789"')
        self.assertRegexpMatches(html, 'name="phones-1-id"[^\>]+value="{}"'.format(
            phone2.pk
        ))
        self.assertEqual(html.count('data-object-id="{}"'.format(phone1.pk)), 1)
        self.assertEqual(html.count('data-object-id="{}"'.format(phone2.pk)), 1)

        self.assertEqual(html.count('data-deletable="1"'), 1)
        self.assertEqual(html.count('data-deletable="0"'), 1)
        self.assertEqual(html.count('data-updatable="0"'), 2)
        self.assertEqual(html.count('data-updatable="1"'), 0)
        self.assertEqual(html.count('selected="selected">Mobile</option>'), 2)
        self.assertFalse('Select a valid choice.' in html)

    def test_validate_create_failure(self):
        data = {
            'name': 'dan man',
            'phones-0-number': '12345678',
            'phones-0-type': ContactPhone.TYPE_LANDLINE,
            'phones-1-type': 'DOH',
            'phones-1-number': '132212',
        }
        form = ContactModelForm(data)
        self.assertFalse(form.is_valid())
        self.assertFalse('name' in form.errors)
        self.assertEqual(form.cleaned_data['name'], 'dan man')
        self.assertTrue('phones' in form.errors)
        self.assertFalse('phones' in form.cleaned_data)
        self.assertEqual(len(form.errors['phones']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="name"[^\>]+value="dan man"')
        self.assertRegexpMatches(html, 'name="phones-0-number"[^\>]+value="12345678"')
        self.assertRegexpMatches(html, 'name="phones-1-number"[^\>]+value="132212"')
        self.assertTrue('Select a valid choice. DOH is not one of the available '
                        'choices.' in html)

    def test_save_new_parent_new_children(self):
        self.assertEqual(Contact.objects.count(), 0)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
                'phones-1-id': '',
            }
        )
        form.is_valid()
        self.assert_form_valid(form)
        instance = form.save()
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIsInstance(instance, Contact)
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.name, 'dan man')
        self.assertEqual(instance.phones.count(), 2)
        phones = list(instance.phones.order_by('pk'))
        self.assertEqual(phones[0].number, '12345678')
        self.assertEqual(phones[0].type, ContactPhone.TYPE_LANDLINE)
        self.assertEqual(phones[1].number, '132212')
        self.assertEqual(phones[1].type, ContactPhone.TYPE_MOBILE)

    def test_save_new_parent_new_children_with_late_commit(self):
        self.assertEqual(Contact.objects.count(), 0)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
            }
        )
        self.assert_form_valid(form)
        instance = form.save(commit=False)
        self.assertEqual(Contact.objects.count(), 0)
        instance.save()
        self.assertEqual(ContactPhone.objects.count(), 0)
        form.save_m2m()
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIsInstance(instance, Contact)
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.name, 'dan man')
        self.assertEqual(instance.phones.count(), 2)
        phones = list(instance.phones.order_by('pk'))
        self.assertEqual(phones[0].number, '12345678')
        self.assertEqual(phones[0].type, ContactPhone.TYPE_LANDLINE)
        self.assertEqual(phones[1].number, '132212')
        self.assertEqual(phones[1].type, ContactPhone.TYPE_MOBILE)

    def test_save_existing_parent_new_children(self):
        contact = Contact.objects.create(name='existing')
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
            },
            instance=contact
        )
        self.assert_form_valid(form)
        instance = form.save()
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIsInstance(instance, Contact)
        self.assertEqual(instance.pk, contact.pk)
        self.assertEqual(instance.name, 'dan man')
        self.assertEqual(instance.phones.count(), 2)
        phones = list(instance.phones.order_by('pk'))
        self.assertEqual(phones[0].number, '12345678')
        self.assertEqual(phones[0].type, ContactPhone.TYPE_LANDLINE)
        self.assertEqual(phones[1].number, '132212')
        self.assertEqual(phones[1].type, ContactPhone.TYPE_MOBILE)

    def test_delete_update_keep_and_add_child(self):
        contact = Contact.objects.create(name='existing')
        deleted_phone = contact.phones.create(number='12345678',
                                              type=ContactPhone.TYPE_LANDLINE)
        updated_phone = contact.phones.create(number='132212',
                                              type=ContactPhone.TYPE_MOBILE,
                                              when_to_call='whenever')
        kept_phone = contact.phones.create(number='5050505',
                                           type=ContactPhone.TYPE_MOBILE,
                                           when_to_call='in the morning')
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ContactPhone.objects.count(), 3)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-DELETE': [deleted_phone.pk],
                # updated phone:
                'phones-1-id': updated_phone.pk,
                'phones-1-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '777777',
                # kept phone:
                'phones-5-id': kept_phone.pk,
                'phones-5-type': kept_phone.type,
                'phones-5-number': kept_phone.number,
                # new phone:
                'phones-369-id': '',
                'phones-369-type': ContactPhone.TYPE_MOBILE,
                'phones-369-number': '369369369',

            },
            instance=contact
        )
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(contact.phones.count(), 3)

        kept_phone = ContactPhone.objects.get(pk=kept_phone.pk)
        self.assertEqual(kept_phone.number, '5050505')
        self.assertEqual(kept_phone.type, ContactPhone.TYPE_MOBILE)
        self.assertEqual(kept_phone.when_to_call, 'in the morning')

        updated_phone = ContactPhone.objects.get(pk=updated_phone.pk)
        self.assertEqual(updated_phone.number, '777777')
        self.assertEqual(updated_phone.type, ContactPhone.TYPE_LANDLINE)
        self.assertEqual(updated_phone.when_to_call, 'whenever')

        added_phone = ContactPhone.objects.order_by('-pk').first()
        self.assertTrue(added_phone.pk > kept_phone.pk)
        self.assertEqual(added_phone.number, '369369369')
        self.assertEqual(added_phone.type, ContactPhone.TYPE_MOBILE)
        self.assertEqual(added_phone.when_to_call, '')

        with self.assertRaises(ContactPhone.DoesNotExist):
            ContactPhone.objects.get(pk=deleted_phone.pk)

    def test_can_not_set_primary_key_on_create(self):
        contact = Contact.objects.create(name='existing')
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '12345678',
                'phones-0-type': ContactPhone.TYPE_LANDLINE,
                'phones-1-number': '132212',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
                'phones-1-id': 66666,
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['pk_override']) in form.as_p()
        )

    def test_can_not_set_primary_key_on_update(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': phone.number,
                'phones-0-type': phone.type,
                'phones-0-id': 66666
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['pk_override']) in form.as_p()
        )

    def test_invalid_delete_ids(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '1111111',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': [phone.pk, 'ABRAKDABRA']
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['invalid_delete_ids'])
            in form.as_p()
        )

    def test_delete_single_multidigit_id(self):
        """Make sure a single deletable id gets converted to a proper list."""
        contact = Contact.objects.create(name='existing')
        phone1 = contact.phones.create(pk=25, number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        phone2 = contact.phones.create(pk=666, number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(contact.phones.count(), 2)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-id': phone1.pk,
                'phones-0-number': '1111111',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': str(phone2.pk)
            },
            instance=contact
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(contact.phones.count(), 1)
        self.assertEqual(contact.phones.first().pk, phone1.pk)

    def test_missing_delete_ids(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '1111111',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': [phone.pk, 66666]
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['missing_delete_ids'])
            in form.as_p()
        )

    def test_update_delete_conflict(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212',
                                      type=ContactPhone.TYPE_MOBILE)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '1111111',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-0-id': phone.pk,
                'phones-DELETE': [phone.pk]
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['update_delete_conflict'])
            in form.as_p()
        )

    def test_protected_delete(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212', type=ContactPhone.TYPE_MOBILE,
                                      delete_lock=True)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '1111112',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': [phone.pk]
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['protected_delete'])
            in form.as_p()
        )

    def test_dont_save_unchanged(self):
        contact = Contact.objects.create(name='existing')
        early_timestamp = (timezone.now() - datetime.timedelta(days=555))\
            .replace(microsecond=0)
        phone = contact.phones.create(number='132212', type=ContactPhone.TYPE_MOBILE)
        contact.phones.update(updated=early_timestamp)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-id': phone.pk,
                'phones-0-number': phone.number,
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': []
            },
            instance=contact
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(contact.phones.count(), 1)
        # Make sure that .save() was not called on the non-changed form
        # (i.e. auto_now=True field hasn't been refreshed).
        self.assertEqual(contact.phones.first().updated, early_timestamp)
        # The changed paremt was still updated
        self.assertEqual(contact.name, 'dan man')

    def test_protected_update_nothing_changed(self):
        contact = Contact.objects.create(name='existing')
        early_timestamp = (timezone.now() - datetime.timedelta(days=555))\
            .replace(microsecond=0)
        phone = contact.phones.create(number='132212', type=ContactPhone.TYPE_MOBILE,
                                      update_lock=True)
        contact.phones.update(updated=early_timestamp)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-id': phone.pk,
                'phones-0-number': phone.number,
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': []
            },
            instance=contact
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(contact.phones.count(), 1)
        self.assertEqual(contact.phones.first().updated, early_timestamp)

    def test_protected_update_change_attempted(self):
        contact = Contact.objects.create(name='existing')
        phone = contact.phones.create(number='132212', type=ContactPhone.TYPE_MOBILE,
                                      update_lock=True)
        self.assertEqual(Contact.objects.count(), 1)
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-id': phone.pk,
                'phones-0-number': phone.number + '1',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-DELETE': []
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['phones'].error_messages['protected_update'])
            in form.as_p()
        )

    def test_min_forms_limit(self):
        contact = Contact.objects.create(name='existing')
        form = ContactModelForm(
            data={
                'name': 'dan man',
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            "At least 1 entry is required."
            in form.as_p()
        )

    def test_max_forms_limit(self):
        contact = Contact.objects.create(name='existing')
        form = ContactModelForm(
            data={
                'name': 'dan man',
                'phones-0-number': '11111111',
                'phones-0-type': ContactPhone.TYPE_MOBILE,
                'phones-1-number': '11111112',
                'phones-1-type': ContactPhone.TYPE_MOBILE,
                'phones-2-number': '11111113',
                'phones-2-type': ContactPhone.TYPE_MOBILE,
                'phones-3-number': '11111114',
                'phones-3-type': ContactPhone.TYPE_MOBILE,
                'phones-4-number': '11111115',
                'phones-4-type': ContactPhone.TYPE_MOBILE,
            },
            instance=contact
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            "At most 4 entries are allowed."
            in form.as_p()
        )


@override_settings(LANGUAGE_CODE='en')
class ModelFormInlineFormTest(TestCase):
    multi_db = True

    def assert_form_valid(self, form):
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        cleaned = form.cleaned_data
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(cleaned['profile']), 3)
        self.assertEqual(cleaned['username'], 'puppet')
        self.assertEqual(cleaned['profile']['first_name'], 'Mr.')
        self.assertEqual(cleaned['profile']['last_name'], 'Puppet')
        self.assertEqual(cleaned['profile']['dob'], date(1969, 6, 9))

    def test_render_empty_form(self):
        form = UserModelForm()
        html = force_text(form)
        self.assertEqual(html.count(' name="profile-dob"'), 1)

    def test_empty_data_errors(self):
        form = UserModelForm(data={})
        self.assertFalse(form.is_valid())
        html = force_text(form)
        self.assertEqual(html.count('This field is required'), 4)

    def test_initial_from_instance(self):
        user = User.objects.create(username='puppet')
        Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                               dob=date(1969, 6, 9))
        form = UserModelForm(instance=user)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html, 'name="profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="profile-last_name"[^\>]+value="Puppet"')
        self.assertRegexpMatches(html, 'name="profile-dob"[^\>]+value="1969-06-09"')
        self.assertFalse('Enter a valid date.' in html)

    def test_initial_after_failed_validation(self):
        user = User.objects.create(username='puppet')
        profile = Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                                         dob=date(1969, 6, 9))
        form = UserModelForm(
            data={
                'username': '',
                'profile-first_name': profile.first_name,
                'profile-last_name': profile.last_name,
                'profile-dob': '1969-06-09',
            },
            instance=user
        )
        self.assertFalse(form.is_valid())
        html = force_text(form)
        
        self.assertRegexpMatches(html, 'name="profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="profile-last_name"[^\>]+value="Puppet"')
        self.assertRegexpMatches(html, 'name="profile-dob"[^\>]+value="1969-06-09"')
        self.assertFalse('Enter a valid date.' in html)

    def test_validate_create_failure(self):
        user = User.objects.create(username='puppet')
        profile = Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                                         dob=date(1969, 6, 9))
        form = UserModelForm(
            data={
                'username': user.username,
                'profile-first_name': profile.first_name,
                'profile-last_name': profile.last_name,
                'profile-dob': '123',
            },
            instance=user
        )
        self.assertFalse(form.is_valid())
        self.assertFalse('username' in form.errors)
        self.assertEqual(form.cleaned_data['username'], 'puppet')
        self.assertTrue('profile' in form.errors)
        self.assertFalse('profile' in form.cleaned_data)
        self.assertEqual(len(form.errors['profile']), 1)
        html = force_text(form)
        self.assertRegexpMatches(html, 'name="username"[^\>]+value="puppet"')
        self.assertRegexpMatches(html, 'name="profile-first_name"[^\>]+value="Mr."')
        self.assertRegexpMatches(html, 'name="profile-last_name"[^\>]+value="Puppet"')
        self.assertTrue('Enter a valid date.' in html)

    def test_save_new_parent_new_child(self):
        self.assertEqual(User.objects.count(), 0)
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppet",
                'profile-dob': '1969-06-09',
            }
        )
        self.assert_form_valid(form)
        instance = form.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertIsInstance(instance, User)
        self.assertIsNotNone(instance.pk)
        self.assertIsInstance(instance.profile, Profile)
        self.assertIsNotNone(instance.profile.pk)
        self.assertEqual(instance.username, 'puppet')
        self.assertEqual(instance.profile.first_name, 'Mr.')
        self.assertEqual(instance.profile.last_name, 'Puppet')
        self.assertEqual(instance.profile.dob, date(1969, 6, 9))

    def test_save_new_parent_new_child_with_late_commit(self):
        self.assertEqual(User.objects.count(), 0)
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppet",
                'profile-dob': '1969-06-09',
            }
        )
        self.assert_form_valid(form)
        instance = form.save(commit=False)
        self.assertEqual(User.objects.count(), 0)
        instance.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 0)
        form.save_m2m()
        self.assertEqual(Profile.objects.count(), 1)

        self.assertIsInstance(instance, User)
        self.assertIsNotNone(instance.pk)
        self.assertIsInstance(instance.profile, Profile)
        self.assertIsNotNone(instance.profile.pk)

        self.assertEqual(instance.username, 'puppet')
        self.assertEqual(instance.profile.first_name, 'Mr.')
        self.assertEqual(instance.profile.last_name, 'Puppet')
        self.assertEqual(instance.profile.dob, date(1969, 6, 9))

    def test_save_existing_parent_new_children(self):
        user = User.objects.create(username='puppet_preupdate')
        self.assertEqual(User.objects.count(), 1)
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppet",
                'profile-dob': '1969-06-09',
            },
            instance=user
        )
        self.assert_form_valid(form)
        instance = form.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertIsInstance(instance, User)
        self.assertEqual(instance.pk, user.pk)
        self.assertEqual(instance.username, 'puppet')
        self.assertEqual(instance.profile.first_name, 'Mr.')
        self.assertEqual(instance.profile.last_name, 'Puppet')
        self.assertEqual(instance.profile.dob, date(1969, 6, 9))

    def test_dont_save_unchanged(self):
        user = User.objects.create(username='puppet_preupdate')
        Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                               dob=date(1969, 6, 9))
        early_timestamp = (timezone.now() - datetime.timedelta(days=555))\
            .replace(microsecond=0)
        Profile.objects.update(updated=early_timestamp)
        user = User.objects.get(pk=user.pk)  # rehydrate User.profile
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppet",
                'profile-dob': '1969-06-09',
            },
            instance=user
        )
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.profile.updated, early_timestamp)
        self.assertEqual(instance.username, 'puppet')

    def test_protected_update_nothing_changed(self):
        user = User.objects.create(username='puppet_preupdate')
        Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                               dob=date(1969, 6, 9), update_lock=True)
        early_timestamp = (timezone.now() - datetime.timedelta(days=555))\
            .replace(microsecond=0)
        Profile.objects.update(updated=early_timestamp)
        user = User.objects.get(pk=user.pk)  # rehydrate User.profile
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppet",
                'profile-dob': '1969-06-09',
            },
            instance=user
        )
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.profile.updated, early_timestamp)
        self.assertEqual(instance.username, 'puppet')

    def test_protected_update_change_attempted(self):
        user = User.objects.create(username='puppet_preupdated')
        Profile.objects.create(user=user, first_name='Mr.', last_name='Puppet',
                               dob=date(1969, 6, 9), update_lock=True)
        self.assertEqual(User.objects.count(), 1)
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppetteer",
                'profile-dob': '1969-06-09',
            },
            instance=user
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['profile'].error_messages['protected_update'])
            in form.as_p()
        )

    def test_protected_create_attempted(self):
        user = User.objects.create(username='puppet_preupdated')
        self.assertEqual(User.objects.count(), 1)
        form = UserModelForm(
            data={
                'username': "puppet",
                'profile-first_name': "Mr.",
                'profile-last_name': "Puppetteer",
                'profile-dob': '1899-06-09',
            },
            instance=user
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            force_text(form.fields['profile'].error_messages['protected_create'])
            in form.as_p()
        )


# TODO: override_settings happens too late?
@skipUnless('bootstrap3' in settings.INSTALLED_APPS, 'bootstrap3 required')
@override_settings(
    BOOTSTRAP3={
        'field_renderers': {
            'default': '.'.join(tuple(__package__.split('.')[:-1]) +
                                ('forms.renderers.InlineFormRenderer', )),
        }
    }
)
class InlineFormBootstrapRenderingTest(TestCase):
    def test_inline_model_form_template(self):
        form = UserModelForm(
            {
                'username': 'puppet',
                'profile-last_name': 'Puppet',
            }
        )
        tmpl = """
        {% load bootstrap3 %}

        {% bootstrap_form form %}
        """
        html = Template(tmpl).render(Context({'form': form}))
        self.assertEqual(html.count('has-success'), 2)  # username, last name
        self.assertEqual(html.count('has-error'), 2)  # first name, dob
        self.assertEqual(html.count('class="form-control id_formidable'), 0)
        # .form-control should have been prevented by the field renderer:
        self.assertEqual(html.count('class="form-control formidable-inline-form'), 0)

    def test_inline_model_formset_template(self):
        form = ContactModelForm(
            data={
                'name': '',
                'phones-0-number': '1232',
                'phones-0-type': 'very bad type',
            }
        )
        tmpl = """
        {% load bootstrap3 %}
        {% bootstrap_form form %}
        """
        html = Template(tmpl).render(Context({'form': form}))
        self.assertEqual(html.count('has-success'), 1)
        self.assertEqual(html.count('has-error'), 2)
        self.assertRegexpMatches(html, 'class\="[^"]*formidable-formset( |")')
        # .form-control should have been removed by the field renderer:
        self.assertEqual(html.count('class="form-control id_formidable'), 0)


class ModelFormBasicInlineFormMixingTest(TestCase):
    def test_empty_rendering(self):
        form = UserModelFormWithBasicProfileForm()
        html = force_text(form)
        self.assertEqual(html.count('name="basic_profile-dob"'), 1)

    def test_rendering_with_instance(self):
        user = User.objects.create(username='puppet')
        form = UserModelFormWithBasicProfileForm(instance=user)
        html = force_text(form)
        self.assertEqual(html.count(' value="puppet"'), 1)
        self.assertEqual(html.count(' name="basic_profile-dob"'), 1)

    def test_saving(self):
        user = User.objects.create(username='puppet')
        form = UserModelFormWithBasicProfileForm(
            data={
                'username': 'puppeteer',
                'basic_profile-first_name': "Mr.",
                'basic_profile-last_name': "Puppetteer",
                'basic_profile-dob': '1899-06-09',
            },
            instance=user
        )
        instance = form.save()
        self.assertEqual(instance.username, 'puppeteer')
        with self.assertRaises(AttributeError):
            type(user.basic_profile)
