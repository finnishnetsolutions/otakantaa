# coding=utf-8

from __future__ import unicode_literals

import hashlib
from uuid import uuid4
from django.contrib.contenttypes.models import ContentType

from django.core import validators
from django.contrib.auth import models as auth
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, ugettext

from imagekit.models.fields import ProcessedImageField, ImageSpecField
from pilkit.processors.resize import SmartResize, ResizeToFit
# from actions.models import ActionTypeMixin
from actions.models import ActionTypeMixin


class UserManager(auth.BaseUserManager):
    def filter(self, *args, **kwargs):
        """
        HACK: allow "is_active" use when filtering for compatibility
        with ``django.contrib.auth`` views

        "email" field found in user.settings - hack for django password reset
        """
        if 'is_active' in kwargs:
            active = kwargs.pop('is_active')
            if active:
                kwargs['status'] = self.model.STATUS_ACTIVE
            else:
                kwargs['status__in'] = filter(
                    lambda status: status != self.model.STATUS_ACTIVE,
                    self.model.STATUS_CHOICES
                )
        if 'email__iexact' in kwargs:
            kwargs['settings__email__iexact'] = kwargs['email__iexact']
            kwargs.pop('email__iexact')

        return super(UserManager, self).filter(*args, **kwargs)

    def create_superuser(self, password, **extra_fields):
        extra_fields['is_superuser'] = True
        extra_fields['is_staff'] = True
        user = self.model(username=extra_fields['username'],
                          is_superuser=True, is_staff=True,
                          status=self.model.STATUS_ACTIVE)
        user.set_password(password)
        user.save()
        return User

    def _create_user(self, username, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)


@python_2_unicode_compatible
class User(auth.PermissionsMixin, auth.AbstractBaseUser):
    USERNAME_FIELD = 'username'
    STATUS_AWAITING_ACTIVATION = 0
    STATUS_ACTIVE = 1
    STATUS_ARCHIVED = 5
    STATUS_CHOICES = (
        (STATUS_AWAITING_ACTIVATION,      _("Odottaa aktivointia")),
        (STATUS_ACTIVE,                   _("Aktiivinen")),
        (STATUS_ARCHIVED,                 _("Arkistoitu")),
    )
    # HACKy: USERNAME_SPECS shared with ``accounts.forms.SignupForm``
    USERNAME_SPECS = dict(
        max_length=30,
        help_text=_(
            "Enintään %(count)d merkkiä. Vain kirjaimet, numerot ja "
            "%(special_chars)s ovat sallittuja."
        ) % {'count': 30, 'special_chars': '_'},
        validators=[
            validators.RegexValidator(
                r'^[a-zA-Z0-9_åäöÅÄÖ]+$', _('Syötä kelvollinen käyttäjätunnus.'), 'invalid'
            )
        ]
    )
    username = models.CharField(_("käyttäjänimi"), unique=True, **USERNAME_SPECS)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into '
                                               'this admin site.'))
    status = models.SmallIntegerField(_("tila"), choices=STATUS_CHOICES,
                                      default=STATUS_CHOICES[0][0])
    joined = models.DateTimeField(_("liittynyt"), auto_now_add=True)
    modified = models.DateTimeField(_("muokattu"), auto_now=True)
    organizations = models.ManyToManyField('organization.Organization',
                                           related_name='admins',
                                           through='organization.AdminSettings'
                                           )
    schemes = models.ManyToManyField('content.Scheme', through='content.SchemeOwner')
    objects = UserManager()

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def is_moderator(self):
        return self.groups.filter(name__in=MODERATOR_GROUP_NAMES)

    @cached_property
    def group_names(self):
        return list(self.groups.values_list('name', flat=True))

    def get_short_name(self):
        return "@{}".format(self.username)

    def get_full_name(self):
        return ' '.join(filter(None, [self.settings.first_name,
                                      self.settings.last_name])) or self.get_short_name()

    def get_contact_information(self):
        return "\n".join(filter(None, [self.settings.email, self.settings.phone_number]))

    def get_organizations_joined(self):
        """ Returns related organizations with @ sign and joined with comma. """
        # TODO: Link to the organization's page.
        # TODO: Remake using templates/template tags.
        organizations = ["@{}".format(organization.name)
                         for organization in self.organizations.all()]
        return ", ".join(organizations)

    def get_groups_joined(self):
        # TODO: Remake this for okadmin user list using templates.
        groups = auth.Group.objects.filter(user__id=self.id)
        group_labels_dict = dict(GROUP_LABELS)
        translated = [group_labels_dict[group.name] for group in groups]
        return ", ".join(translated)

    # Deprecated and can be deleted?
    def get_groups_names(self):
        return [group.name for group in auth.Group.objects.filter(user=self)]

    def get_absolute_url(self):
        return reverse('account:profile', kwargs={'user_id': self.pk})

    def facebook_associated(self):
        return self.social_auth.get(provider="facebook") is not None

    @cached_property
    def organization_ids(self):
        return list(self.organizations.values_list('pk', flat=True))

    @property
    def email(self):
        return self.settings.email

    def __str__(self):
        return ''.join(['@', self.username])

    def unread_messages_count(self):
        return self.message_deliveries.filter(read=False).count() or ""

    class Meta:
        verbose_name = _("Käyttäjä")
        verbose_name_plural = _("Käyttäjät")


def _user_profile_pic_path(obj, name):
    return 'user/%d/pictures/%s.jpg' % (obj.pk, uuid4().hex)


class UserSettings(models.Model):
    LANGUAGE_FINNISH = 'fi'
    LANGUAGE_SWEDISH = 'sv'
    LANGUAGE_CHOICES = (
        (LANGUAGE_FINNISH,   _("suomi")),
        (LANGUAGE_SWEDISH,   _("ruotsi")),
    )

    BOOLEAN_CHOICES = {
        True: _("Kyllä"),
        False: _("Ei"),
    }

    user = models.OneToOneField(User, related_name='settings')
    first_name = models.CharField(_("etunimi"), max_length=50)
    last_name = models.CharField(_("sukunimi"), max_length=50)
    language = models.CharField(_("kieli"), choices=LANGUAGE_CHOICES,
                                max_length=5, default=LANGUAGE_CHOICES[0][0])
    email = models.EmailField(_("sähköposti"), max_length=254, unique=True)
    municipality = models.ForeignKey('fimunicipality.Municipality')
    picture = ProcessedImageField(
        upload_to=_user_profile_pic_path,
        processors=[ResizeToFit(width=1280, height=1280, upscale=False)],
        format='JPEG', options={'quality': 90}
    )
    picture_medium = ImageSpecField(source='picture',
                                    processors=[SmartResize(width=220, height=220)],
                                    format='JPEG', options={'quality': 70})
    picture_small = ImageSpecField(source='picture',
                                   processors=[SmartResize(width=46, height=46)],
                                   format='JPEG', options={'quality': 70})

    def get_municipality_display(self):
        return self.municipality

    class Meta:
        verbose_name = _("Käyttäjäasetus")
        verbose_name_plural = _("Käyttäjäasetukset")


GROUP_NAME_MODERATORS = 'moderator'
GROUP_NAME_ADMINS = 'admin'
GROUP_LABELS = (
    (GROUP_NAME_MODERATORS, ugettext("Moderaattori")),
    (GROUP_NAME_ADMINS, ugettext("Ylläpitäjä")),
)
MODERATOR_GROUP_NAMES = [GROUP_NAME_MODERATORS, GROUP_NAME_ADMINS]


class ClientIdentifierManager(models.Manager):
    def get_or_create(self, ip=None, user_agent=None):
        signature = hashlib.md5(ip + user_agent).hexdigest()
        return super(ClientIdentifierManager, self).get_or_create(
            hash=signature, defaults={'ip': ip, 'user_agent': user_agent}
        )


class ClientIdentifier(models.Model):
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    hash = models.CharField(max_length=32, unique=True)

    objects = ClientIdentifierManager()


class NotificationOptions(models.Model, ActionTypeMixin):
    user = models.ForeignKey(User, related_name='user_notifications')
    content_type = models.ForeignKey(ContentType)
    role = models.CharField(max_length=50)
    action_type = models.CharField(max_length=16)
    action_subtype = models.CharField(max_length=100, default='')
    cancelled = models.BooleanField(default=False)
    notify_at_once = models.BooleanField(default=False)
    notify_daily = models.BooleanField(default=False)
    notify_weekly = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super(NotificationOptions, self).__init__(*args, **kwargs)
        self._type_field = 'action_type'
        self._subtype_field = 'action_subtype'

    class Meta:
        unique_together = (('user', 'content_type', 'role', 'action_type',
                            'action_subtype'), )
