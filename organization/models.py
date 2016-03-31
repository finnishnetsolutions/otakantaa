# coding=utf-8

from __future__ import unicode_literals

import bleach
from uuid import uuid4

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, ugettext

from imagekit.models.fields import ProcessedImageField, ImageSpecField
from pilkit.processors.resize import ResizeToFit, SmartResize
# from account.models import User, GROUP_NAME_MODERATORS
# from actions.models import ActionGeneratingModelMixin

from libs.moderation.models import MODERATION_STATUS_APPROVED
from libs.moderation.signals import post_moderation

from otakantaa.models import MultilingualRedactorField, MultilingualTextField
from otakantaa.utils import strip_tags


def _organization_pic_path(obj, name):
    return 'organization/%d/pictures/%s.jpg' % (obj.pk, uuid4().hex)


class OrganizationQuerySet(models.QuerySet):
    def normal(self):
        return self.active()

    def active(self):
        return self.filter(is_active=True)

    def active_or_pending(self):
        id_list = [o.pk for o in self.all() if o.awaits_activation() or o.is_active]
        return self.filter(pk__in=id_list)


@python_2_unicode_compatible
class Organization(models.Model):
    TYPE_PUBLIC_ADMINISTRATION = 1
    TYPE_ORGANIZATION = 2
    TYPE_OTHER = 10
    TYPE_CHOICES = (
        (TYPE_PUBLIC_ADMINISTRATION, _("Julkishallinto")),
        (TYPE_ORGANIZATION,          _("Järjestö")),
        (TYPE_OTHER,                 _("Muu organisaatio")),
    )

    type = models.SmallIntegerField(_("tyyppi"), choices=TYPE_CHOICES)
    name = MultilingualTextField(_("nimi"), max_length=255, simultaneous_edit=True)
    description = MultilingualRedactorField(_("kuvaus"), blank=True)
    municipalities = models.ManyToManyField(
        'fimunicipality.Municipality',
        related_name='organizations',
        verbose_name=_("Kunnat")
    )
    picture = ProcessedImageField(
        upload_to=_organization_pic_path,
        processors=[ResizeToFit(width=1280, height=1280, upscale=False)],
        format='JPEG', options={'quality': 90},
        null=True, default=None, blank=True
    )
    picture_medium = ImageSpecField(source='picture',
                                    processors=[SmartResize(width=220, height=220), ],
                                    format='JPEG', options={'quality': 70})
    is_active = models.BooleanField(_("aktiivinen"), default=False)
    created = models.DateTimeField(_("luotu"), default=timezone.now)
    activated = models.DateTimeField(_("aktivoitu"), default=None, null=True)
    search_text = models.TextField(null=True, default=None)
    twitter_username = models.CharField(max_length=255,
                                        verbose_name="Twitter-käyttäjänimi", blank=True)

    objects = OrganizationQuerySet.as_manager()

    # Use get_schemes property to get distinct schemes owned by organization
    schemes = models.ManyToManyField('content.Scheme', through='content.SchemeOwner')

    def __str__(self):
        return '%s' % self.name

    # Use this property to get distinct schemes owned by organization, because there can
    # be multiple admins from same organization linked to scheme trough SchemeOwner model
    def get_real_schemes(self):
        return self.schemes.filter(owners__approved=True).distinct()

    def get_absolute_url(self):
        return reverse('organization:detail', kwargs={'pk': self.pk})

    def description_plaintext(self):
        desc = '%s' % self.description
        return bleach.clean(desc.replace('>', '> '),
                            tags=[], strip=True, strip_comments=True).strip()

    def admins_str(self):
        admin_list = [a.get_full_name() for a in self.admins.all()]
        return ", ".join(admin_list)

    def awaits_activation(self):
        return not self.is_active and not self.activated

    """
    # action processing
    def action_kwargs_on_create(self):

        return {'actor': None}

    def fill_notification_recipients(self, action):
        for u in User.objects.filter(groups__name=GROUP_NAME_MODERATORS):
            action.add_notification_recipients(action.ROLE_MODERATOR, u)
    """

    FAVORITE_TEXT = ugettext("Seuraa organisaatioita")

    class Meta:
        verbose_name = _("organisaatio")
        verbose_name_plural = _("organisaatiot")


class AdminSettingsQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(approved=True)

    def unapproved(self):
        return self.filter(approved=False)

@python_2_unicode_compatible
class AdminSettings(models.Model):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    user = models.ForeignKey('account.User', on_delete=models.CASCADE)
    approved = models.BooleanField(default=True)
    objects = AdminSettingsQuerySet.as_manager()

    def __str__(self):
        return "{}, {}".format(self.user, self.organization)

    class Meta:
        verbose_name = _("yhteyshenkilö")
        verbose_name_plural = _("yhteyshenkilöt")


@receiver(signal=post_moderation, sender=Organization)
def activate_approved_organization(instance=None, status=None, **kwargs):
    if status == MODERATION_STATUS_APPROVED and not instance.is_active:
        instance.is_active = True
        instance.save()


@receiver(pre_save, sender=Organization)
def update_search_text(instance=None, **kwargs):
    instance.search_text = ' '.join(map(strip_tags, instance.name.values() +
                                        instance.description.values()))
