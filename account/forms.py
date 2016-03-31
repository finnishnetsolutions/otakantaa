# coding=utf-8

from __future__ import unicode_literals

import hashlib
import logging

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.forms.models import ModelChoiceField
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from libs.djcontrib.forms.forms import FieldReAttrMixIn
from libs.djcontrib.forms.widgets import NoAutocompletePasswordInput
from libs.fimunicipality.models import Municipality

from actions.lists import NOTIFICATION_OPTIONS
from actions.models import Action
from account.models import GROUP_NAME_MODERATORS, NotificationOptions
from okmessages.models import Message
from organization.models import Organization
from otakantaa.forms.fields import ModelMultipleChoiceField
from otakantaa.forms.widgets import Select2, AutoSubmitButtonSelect

from .models import User, UserSettings

logger = logging.getLogger(__name__)


class UserForm(FieldReAttrMixIn, UserCreationForm):
    field_widgets = (
        ('password1', NoAutocompletePasswordInput(render_value=True)),
        ('password2', NoAutocompletePasswordInput(render_value=True))
    )
    username = forms.CharField(label=_("Käyttäjätunnus"), **User.USERNAME_SPECS)
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    def clean_username(self):
        # HACK: Copy-paste from ``django.contirb.auth.forms.UserCreationForm``,
        # because it uses hardcoded ``auth.User`` model class.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    class Meta:
        fields = ('username',)
        model = User


class LoginForm(FieldReAttrMixIn, AuthenticationForm):
    field_widgets = (
        ('password', NoAutocompletePasswordInput()),
    )
    error_messages = {
        'invalid_login': _("Virheellinen käyttäjätunnus tai salasana."),
        'inactive': _("Käyttäjätunnus ei ole aktiivinen."),
    }


class UserSettingsForm(forms.ModelForm):

    municipality = forms.ModelChoiceField(
        label=_("Kotikunta"), queryset=Municipality.objects.natural().active(),
        widget=Select2, required=True, empty_label=_("Valitse")
    )

    def clean_email(self):
        username = self.cleaned_data.get('email', None)
        if username:
            if bool(self._meta.model._default_manager.filter(email=username)):
                raise forms.ValidationError(_("Sähköpostiosoite on jo käytössä."))
        return username

    class Meta:
        fields = ('first_name', 'last_name', 'email', 'language', 'municipality', )
        model = UserSettings


class UserSignUpForm(UserSettingsForm):

    connect_to_organization = forms.BooleanField(
        required=False, label=_("Olen organisaation edustaja"),
    )

    existing_organization = ModelChoiceField(
        queryset=Organization.objects.normal(),
        label=_("Valitse organisaatio"), required=False, empty_label=_("Valitse"),
        help_text=_("...tai jätä kenttä tyhjäksi ja luo uusi organisaatio täyttämällä "
                    "alla oleva kenttä."),
        widget=Select2,
    )

    new_organization = forms.CharField(max_length=500, min_length=1, required=False,
                                       label=_("Kirjoita edustamasi organisaation nimi"))

    def clean(self):
        cleaned = super(UserSignUpForm, self).clean()
        if cleaned['connect_to_organization']:
            if not cleaned['existing_organization'] and not cleaned['new_organization']:
                self.add_error('existing_organization', _("Valitse organisaatio"))
                self.add_error('new_organization', _("Kirjoita organisaation nimi"))
        return cleaned

    class Meta:
        fields = ('email', 'first_name', 'last_name', 'language', 'municipality',
                  'connect_to_organization', )
        model = UserSettings


class EmailConfirmationForm(forms.ModelForm):
    XORER = 7010394

    generic_error = _("Vahvistuslinkki on virheellinen tai vanhentunut.")

    token = forms.CharField(min_length=25, max_length=50)

    @classmethod
    def hashables(cls, user):
        last_login = None
        if user.last_login:
            last_login = user.last_login.replace(microsecond=0, tzinfo=None)
        hash_list = [user.password,
                     last_login,
                     cls.__name__,
                     settings.SECRET_KEY]
        return hash_list

    @classmethod
    def create_token(cls, user):
        hashable = '|'.join(map(str, cls.hashables(user)))
        token = hashlib.sha512(hashable).hexdigest()[:25] + ('%x' % (cls.XORER ^ user.pk))
        logger.debug('EmailConfirmationForm.create_token(): %s => %s',
                     hashable, token)
        return token

    def clean(self):
        cleaned_data = super(EmailConfirmationForm, self).clean()
        if 'token' in cleaned_data:
            try:
                user_id = self.XORER ^ int(cleaned_data['token'][25:], 16)
            except ValueError:
                logger.debug('Poletista "%s" parsittu käyttäjä id '
                             'ei ollut kelvollinen numero.' %
                             cleaned_data['token'])
                raise self.GenericError()

            try:
                user = self._meta.model._default_manager.get(pk=user_id)
            except User.DoesNotExist:
                logger.debug('Käyttäjää #%d ei löytynyt.' % user_id)
                raise self.GenericError()

            valid_token = self.__class__.create_token(user)

            if cleaned_data['token'] != valid_token:
                logger.debug('Virheellinen token käyttäjälle #%d: "%s" '
                             '(haluttiin "%s").' % (user_id,
                                                    cleaned_data['token'],
                                                    valid_token))
                raise self.GenericError()

            cleaned_data['user'] = user

        return cleaned_data

    @transaction.atomic()
    def save(self, commit=True):
        assert commit is True, "EmailConfirmationForm.save() requires commit=True"
        self.activate_user(self.cleaned_data['user'])
        return self.cleaned_data['user']

    def activate_user(self, user):
        user = self.cleaned_data['user']
        if user.status == self._meta.model.STATUS_AWAITING_ACTIVATION:
            user.status = self._meta.model.STATUS_ACTIVE
            user.save()

    class GenericError(forms.ValidationError):
        def __init__(self, *args, **kwargs):
            forms.ValidationError.__init__(self, EmailConfirmationForm.generic_error)

    class Meta:
        model = User
        fields = ('token', )


class UserSettingsDetailForm(forms.ModelForm):

    class Meta:
        model = UserSettings
        fields = ('first_name', 'last_name', 'email', 'language', 'municipality', )


class UserSettingsEditForm(UserSettingsDetailForm, UserSettingsForm):

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        return email


class EditProfilePictureForm(forms.ModelForm):
    picture = forms.ImageField(label=_("Uusi kuva"), widget=forms.FileInput,
                               required=False)

    class Meta:
        model = UserSettings
        fields = ('picture', )


class MessageForm(forms.ModelForm):
    receivers = ModelMultipleChoiceField(
        label=_("Valitse vastaanottajat"),
        queryset=User.objects.filter(is_active=True)
    )
    message = forms.CharField(label=_('Viesti'), widget=forms.Textarea)

    def get_moderator_receivers_queryset(self, user):
        return User.objects.filter(is_active=True).exclude(pk=user.pk)

    def get_contactperson_receivers_queryset(self, user):
        return User.objects.filter(is_active=True).exclude(pk=user.pk)

    def get_participant_receivers_queryset(self, user):
        receivers_queryset = User.objects.annotate(
            organizations_count=Count('organizations')
        ).filter(Q(groups__name=GROUP_NAME_MODERATORS) | Q(organizations_count__gt=0),
                 status=User.STATUS_ACTIVE).exclude(pk=user.pk)
        return receivers_queryset

    def __init__(self, user, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        if user.is_moderator:
            receivers_queryset = self.get_moderator_receivers_queryset(user)
        elif user.organizations.count():
            receivers_queryset = self.get_contactperson_receivers_queryset(user)
        else:
            receivers_queryset = self.get_participant_receivers_queryset(user)

        self.fields["receivers"].queryset = receivers_queryset

    class Meta:
        model = Message
        fields = ("receivers", "subject", "message", )


class UserProfileSchemeListForm(forms.ModelForm):
    KEY_CHOICES = [
        ('',  _("Omat")),
        ('content.scheme', _("Seuratut hankkeet")),
        ('tagging.tag', _("Seuratut aiheet")),
        ('organization.organization', _("Seuratut organisaatiot")),
        ('fimunicipality.municipality', _("Seuratut kunnat")),
        ('affected', _("Osallistumiset hankkeissa")),
    ]

    ct_natural_key = forms.ChoiceField(choices=KEY_CHOICES, widget=AutoSubmitButtonSelect,
                                       required=False, label=_("Näytä"))

    def save(self, commit=True):
        raise Exception("Ei salllittu")

    class Meta:
        model = User
        fields = ('ct_natural_key', )


class UsernameForm(forms.ModelForm):
    username = forms.CharField(label=_("Käyttäjätunnus"), **User.USERNAME_SPECS)

    def __init__(self, disable_helptext=False, *args, **kwargs):
        super(UsernameForm, self).__init__(*args, **kwargs)
        self.user = kwargs["instance"]

        if disable_helptext:
            username_specs = User.USERNAME_SPECS.copy()
            try:
                del username_specs["help_text"]
            except KeyError:
                pass
            self.fields["username"] = forms.CharField(
                label=_("Käyttäjätunnus"), **username_specs
            )

    def clean_username(self):
        # HACK: Copy-paste from ``django.contirb.auth.forms.UserCreationForm``,
        # because it uses hardcoded ``auth.User`` model class.
        username = self.cleaned_data["username"]

        # Allow the same username to be saved that is currently already used.
        if username.lower() == self.user.username.lower():
            return username

        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            _("Käyttäjätunnus on jo käytössä."),
            code='duplicate_username',
        )

    class Meta:
        model = User
        fields = ("username",)


class NotificationOptionsForm(forms.ModelForm):

    OPTION_PREFIX = 'opt_'
    INITIAL_CMP_FIELDS = {'model', 'role', 'action_type', 'action_subtype'}
    INITIAL_FIELDS = {'notify', 'notify_at_once', 'notify_daily', 'notify_weekly'}


    @staticmethod
    def dict_extract(my_dict, fields_to_extract):
        return {key: value for key, value in my_dict.items() if key in fields_to_extract}

    def get_initials(self, option, un_list):
        # check if option row has match in un_list (user_notifications)
        cmp_dict1 = self.dict_extract(option, self.INITIAL_CMP_FIELDS)
        for row in un_list:
            cmp_dict2 = self.dict_extract(row, self.INITIAL_CMP_FIELDS)
            if cmp(cmp_dict1, cmp_dict2) == 0:
                initial_dict = self.dict_extract(row, self.INITIAL_FIELDS)
                return [key for key, value in initial_dict.items() if value is True]
        return []

    def notification_types(self):
        types = [Action.USER_TYPE_NORMAL, ]
        if self.instance.is_moderator:
            types.append(Action.USER_TYPE_MODERATOR)
        if self.instance.organization_ids:
            types.append(Action.USER_TYPE_CONTACT_PERSON)
        return types

    def get_options(self):
        user_types = self.notification_types()
        options = []
        for index, option in enumerate(NOTIFICATION_OPTIONS):
            if any([item in user_types for item in option['group']]):
                options.append(option)
        return options

    def __init__(self, *args, **kwargs):
        super(NotificationOptionsForm, self).__init__(*args, **kwargs)
        un_list = self.instance.user_notifications.all().values()

        for v in un_list:
            v['model'] = ContentType.objects.get_for_id(v['content_type_id'])\
                .model_class()
            v['notify'] = not v['cancelled']

        for index, option in enumerate(self.get_options()):
            choices = (
                ('notify', option['label']),
                ('notify_at_once', _("Heti")),
                ('notify_daily', _("Päivittäin")),
                ('notify_weekly', _("Viikottain")),
            )

            self.fields[self.OPTION_PREFIX+'{}'.format(index)] = forms.\
                MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                    choices=choices, label='', required=False,
                                    initial=self.get_initials(option, un_list))

    def clean(self):
        cleaned_data = super(NotificationOptionsForm, self).clean()
        for k, row in cleaned_data.iteritems():
            # removing unnecessary elements and setting 'cancelled' switch
            if 'notify' not in row:
                cleaned_data[k] = ['cancelled', ]
        return cleaned_data

    @transaction.atomic()
    def save(self, commit=True):
        assert commit is True, 'Must commit'

        user = self.instance
        NotificationOptions.objects.filter(user=user).delete()
        for index, option in enumerate(self.get_options()):
            field_key = NotificationOptionsForm.OPTION_PREFIX + str(index)
            obj = NotificationOptions()
            obj.user = user
            obj.role = option['role']
            obj.content_type = ContentType.objects.get_for_model(option['model'],
                                                                 for_concrete_model=False)
            obj.action_type = option['action_type']
            if 'action_subtype' in option:
                obj.action_subtype = option['action_subtype']

            if field_key in self.cleaned_data:
                for field in self.cleaned_data[field_key]:
                    setattr(obj, field, True)

            obj.save()

    class Meta:
        model = User
        fields = []

