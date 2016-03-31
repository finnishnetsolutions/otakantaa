# coding=utf-8

from __future__ import unicode_literals

from datetime import datetime, timedelta
from django.template.loader import render_to_string

from django.utils.functional import cached_property
from imagekit.models.fields import ProcessedImageField, ImageSpecField
from kombu.utils import uuid4
from pilkit.processors.resize import ResizeToFit, Resize
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.template.defaultfilters import date
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.utils.encoding import python_2_unicode_compatible

from account.models import User
from favorite.models import Favorite
from organization.models import Organization
from otakantaa.models import MultilingualTextField, MultilingualRedactorField
from otakantaa.utils import strip_tags, send_email


def _scheme_main_pic_path(obj, name):
    return 'scheme/%d/pictures/%s.jpg' % (obj.pk, uuid4().hex)


class ResizeToMinimumDimensions(object):
    def __init__(self, width=None, height=None):
        self.width, self.height = width, height

    def process(self, img):
        cur_width, cur_height = img.size
        if self.width is not None and self.height is not None:
            ratio = max(float(self.width) / cur_width,
                        float(self.height) / cur_height)
        else:
            if self.width is None:
                ratio = float(self.height) / cur_height
            else:
                ratio = float(self.width) / cur_width
        new_dimensions = (int(round(cur_width * ratio)),
                          int(round(cur_height * ratio)))
        img = Resize(new_dimensions[0], new_dimensions[1], upscale=True).process(img)
        return img


class SchemeQuerySet(models.QuerySet):
    def public(self):
        return self.filter(visibility=Scheme.VISIBILITY_PUBLIC).order_by('-published')


@python_2_unicode_compatible
class Scheme(models.Model):
    STATUS_DRAFT = 0
    STATUS_PUBLISHED = 3
    STATUS_CLOSED = 6
    STATUSES = (
        (STATUS_DRAFT, 'created', _("Luonnos")),
        (STATUS_PUBLISHED, 'published', _("Julkaistu")),
        (STATUS_CLOSED, 'closed', _("Päättynyt")),
    )
    STATUS_CHOICES = [(s[0], s[2]) for s in STATUSES]

    title = MultilingualTextField(_("otsikko"), max_length=255, simultaneous_edit=True)
    lead_text = MultilingualTextField(_("tiivistelmä"), max_length=500,
                                      simultaneous_edit=True)
    summary = MultilingualRedactorField(_("yhteenveto"), max_length=500,
                                        simultaneous_edit=True)
    description = MultilingualRedactorField(_("lisätieto"), blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # creator == User who initially created the object, not displayed in the UI
    creator = models.ForeignKey('account.User', null=True, on_delete=models.SET_NULL,
                                related_name='creator')
    # modifier == User who initially modified the object, not displayed in the UI
    modifier = models.ForeignKey('account.User', null=True, on_delete=models.SET_NULL,
                                 related_name='modifier')
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(null=True, default=None, blank=True)
    closed = models.DateTimeField(null=True, default=None, blank=True)

    VISIBILITY_DRAFT = 1
    VISIBILITY_ARCHIVED = 8
    VISIBILITY_PUBLIC = 10
    VISIBILITIES = (
        (VISIBILITY_DRAFT, '', _("Luonnos")),
        (VISIBILITY_PUBLIC, '', _("Julkinen")),
        (VISIBILITY_ARCHIVED, 'archived', _("Arkistoitu")),
    )
    VISIBILITY_CHOICES = [(s[0], s[2]) for s in VISIBILITIES]

    INTERACTION_EVERYONE = 1
    INTERACTION_REGISTERED_USERS = 2
    INTERACTION_CHOICES = (
        (INTERACTION_EVERYONE, _("Kaikki")),
        (INTERACTION_REGISTERED_USERS, _("Rekisteröityneet käyttäjät")),
    )

    visibility = models.SmallIntegerField(_("näkyvyys"),
                                          choices=VISIBILITY_CHOICES,
                                          default=VISIBILITY_DRAFT)

    interaction = models.SmallIntegerField(_("Kuka saa ottaa kantaa, vastata kyselyyn ja "
                                             "ottaa osaa keskusteluun?"),
                                           choices=INTERACTION_CHOICES,
                                           default=INTERACTION_EVERYONE)

    # Large picture, to be used as a source for pictures actually displayed on the site
    picture = ProcessedImageField(
        upload_to=_scheme_main_pic_path,
        processors=[ResizeToFit(width=1280, height=1280 * 4, upscale=False)],
        format='JPEG', options={'quality': 90}
    )

    # Medium picture, to be displayed on the Scheme page, with some effort to make it
    # fixed width
    picture_main = ImageSpecField(source='picture',
                                  processors=[
                                      ResizeToMinimumDimensions(width=710),
                                      ResizeToFit(width=710, height=4 * 710),
                                  ], format='JPEG', options={'quality': 70})

    # Narrow picture, to be displayed on grids with multiple Schemes, cropping allowed
    picture_narrow = ImageSpecField(source='picture',
                                    processors=[ResizeToMinimumDimensions(width=350),
                                                ResizeToFit(width=350, height=4 * 350)],
                                    format='JPEG', options={'quality': 70})

    picture_alt_text = models.CharField(_("kuvan tekstimuotoinen kuvaus (suositeltava)"),
                                        max_length=255,
                                        default=None,
                                        null=True)
    archived = models.DateTimeField(null=True, default=None, blank=True)

    premoderation = models.BooleanField(_("kommenttien esimoderointi"), default=False)
    tags = models.ManyToManyField('tagging.Tag', verbose_name=_("aiheet"))
    target_municipalities = models.ManyToManyField('fimunicipality.Municipality',
                                                   related_name='targeted_schemes',
                                                   verbose_name=_("kohdekunnat"))
    upload_group = GenericRelation('attachtor.UploadGroup')
    twitter_search = models.CharField(max_length=255, blank=True,
                                      verbose_name=_("Twitter-hakusana"))
    search_text = models.TextField(default=None, null=True)

    objects = SchemeQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.pk})

    def is_public(self):
        return self.visibility in (Scheme.VISIBILITY_PUBLIC, Scheme.VISIBILITY_ARCHIVED)

    @property
    def attachments(self):
        if self.upload_group.count():
            return self.upload_group.first().upload_set
        return None

    @cached_property
    def owner_ids(self):
        return list(self.owners.real().values_list('user_id', flat=True))

    def status_date(self):
        for status_id, status_field, status_verbal in self.STATUSES:
            if status_id == self.status:
                return date(getattr(self, status_field), 'SHORT_DATE_FORMAT')

    def html_allowed(self):
        return True

    def conversation_comment_count(self, days_backward=False):
        if days_backward:
            time_filter = timezone.now() - timedelta(days=days_backward)
        count = 0
        for pd in self.participations.conversations():
            qs = pd.content_object.comments.public()
            if days_backward:
                count += qs.filter(created__gte=time_filter).count()
            else:
                count += qs.count()
        return count

    def survey_submission_count(self, days_backward=False):
        if days_backward:
            time_filter = timezone.now() - timedelta(days=days_backward)
        count = 0
        for pd in self.participations.surveys():
            qs = pd.content_object.submissions
            if days_backward:
                count += qs.filter(created__gte=time_filter).count()
            else:
                count += qs.count()
        return count

    def has_been_participated(self):
        if self.survey_submission_count() or self.conversation_comment_count():
            return True
        return False

    def __str__(self):
        return '%s' % self.title

    def description_plaintext(self):
        # @attention: extra string conversion to get description for active language
        return strip_tags('%s' % self.description)

    def written_as_organization(self):
        return True if self.owners.filter(organization_id__isnull=False).count() \
            else False

    def status_complete(self):
        for sid, date_field, text in self.STATUSES:
            if sid == self.status:
                status_text = text
                if self.status != ParticipationDetails.STATUS_DRAFT:
                    status_text = "{}: {}".format(
                        status_text,
                        date(getattr(self, date_field), 'SHORT_DATE_FORMAT'))
                return status_text
        return ""

    def fill_notification_recipients(self, action):
        # owners
        for u in self.owners.unique_users():
            action.add_notification_recipients(action.ROLE_CONTENT_OWNER, u)

        # followers
        followings = Favorite.objects.filter(
            content_type=ContentType.objects.get_for_model(Scheme),
            object_id=self.pk,
        ).all()
        for f in followings:
            action.add_notification_recipients(action.ROLE_CONTENT_FOLLOWER, f.user)

    def last_participation_date(self):
        d = datetime.min.date()
        for p in self.participations.all():
            p_date = p.last_participation_date()
            if not d:
                d = p_date
                continue
            d = d if d > p_date else p_date
        return d

    @property
    def popularity(self):
        return self.comments_and_submissions_count()

    def comments_and_submissions_count(self, days_backward=False):
        return self.conversation_comment_count(days_backward) + \
               self.survey_submission_count(days_backward)

    @property
    def hotness(self):
        d = settings.HOT_DAYS
        hot = self.comments_and_submissions_count(d)
        normal = self.comments_and_submissions_count()
        if hot:
            hot += settings.HOTNESS_POINTS
        return hot + normal

    def get_participators(self):
        user_ids = []
        for p in self.participations.all():
            user_ids.extend(p.get_involved_user_ids())
        return User.objects.filter(pk__in=list(set(user_ids)))

    @property
    def is_organization_scheme(self):
        return self.owners.filter(organization__isnull=False).count()

    """
    def last_participated_or_modified_date(self):
        last_p_date = self.last_participation_date()
        return self.modified.date() if self.modified.date() > last_p_date else last_p_date
    """


@receiver(pre_save, sender=Scheme)
def update_search_text(instance=None, **kwargs):
    instance.search_text = ' '.join(map(strip_tags,
                                        instance.description.values()
                                        + instance.title.values()
                                        + instance.lead_text.values()
                                        ))


class SchemeOwnerQuerySet(models.QuerySet):
    def unique_organizations(self):
        pk_list = self.real().values_list('organization_id', flat=True)
        return Organization.objects.filter(pk__in=pk_list)

    def unique_users(self):
        pk_list = self.real().values_list('user_id', flat=True)
        return User.objects.filter(pk__in=pk_list)

    def real(self):
        return self.filter(approved=True)

    def unapproved(self):
        return self.filter(approved=False)

    def schemes(self):
        return Scheme.objects.filter(
            pk__in=list(self.values_list('scheme_id', flat=True))
        )


@python_2_unicode_compatible
class SchemeOwner(models.Model):
    scheme = models.ForeignKey(Scheme, related_name='owners')
    user = models.ForeignKey('account.User', related_name='owned_schemes')
    organization = models.ForeignKey('organization.Organization', null=True,
                                     related_name='owned_schemes')

    STATE_CHOICES = (
        (True, _("Kyllä")),
        (False, _("Ei")),
    )
    # approved by invited user
    approved = models.BooleanField(default=False, choices=STATE_CHOICES,
                                   verbose_name=_("Hyväksy kutsu"))
    objects = SchemeOwnerQuerySet.as_manager()

    def __str__(self):
        if self.organization:
            return "{}: {}".format(self.organization, self.user)
        return "%s" % self.user

    def get_short_name(self):
        org = "{}: ".format(self.organization) if self.organization else ""
        return "{}{}".format(org, self.user.get_short_name())

    def get_absolute_url(self):
        if self.organization:
            return self.organization.get_absolute_url()
        return self.user.get_absolute_url()

    def get_form_field_value(self):
        return "{}:{}".format(self.user_id, self.organization_id)

    class Meta:
        unique_together = ('scheme', 'user', 'organization',)


def get_invitation_url(scheme_owner):
    return reverse('content:owner_invitation', kwargs={
        'scheme_owner_id': scheme_owner.pk, 'scheme_id': scheme_owner.scheme.pk})


@receiver(post_save, sender=SchemeOwner)
def send_invitation(instance=None, **kwargs):
    if kwargs['created'] and not instance.approved:
        options = {
            'scheme': instance.scheme,
            'invitation_url': get_invitation_url(instance)
        }

        if instance.organization:
            options.update({'organization': instance.organization})
            email_template = 'scheme/email/owner_organization_invitation.txt'
        else:
            email_template = 'scheme/email/owner_invitation.txt'

        send_email(
            _("Kutsu hankkeen omistajaksi"),
            email_template,
            options,
            [instance.user.settings.email],
            instance.user.settings.language
        )


class ParticipationQuerySet(models.QuerySet):
    def conversations(self):
        conversation_ct = ContentType.objects \
            .get_by_natural_key('conversation', 'conversation')
        return self.filter(content_type=conversation_ct)

    def surveys(self):
        survey_ct = ContentType.objects.get_by_natural_key('survey', 'survey')
        return self.filter(content_type=survey_ct)

    def ready_to_publish(self):
        id_list = [x.pk for x in self.all() if x.ready_to_publish()]
        return self.filter(id__in=id_list)

    def ready_to_close(self):
        id_list = [x.pk for x in self.all() if x.ready_to_close()]
        return self.filter(id__in=id_list)

    def open(self):
        id_list = [x.pk for x in self.all() if x.is_open()]
        return self.filter(id__in=id_list)

    def open_or_draft(self):
        id_list = [x.pk for x in self.all() if x.is_open() or x.is_draft()]
        return self.filter(id__in=id_list)

    def closed(self):
        id_list = [x.pk for x in self.all() if x.is_expired()]
        return self.filter(id__in=id_list)

    def published(self):
        return self.exclude(status=ParticipationDetails.STATUS_DRAFT)


@python_2_unicode_compatible
class ParticipationDetails(models.Model):
    STATUS_DRAFT = 0
    STATUS_PUBLISHED = 3
    STATUSES = (
        (STATUS_DRAFT, 'created', _("Luonnos")),
        (STATUS_PUBLISHED, 'opened', _("Avoin")),
    )
    STATUS_CHOICES = [(s[0], s[2]) for s in STATUSES]

    title = MultilingualTextField(_("otsikko"), max_length=255, simultaneous_edit=True)
    description = MultilingualRedactorField(_("kuvaus"), blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created = models.DateTimeField(default=timezone.now)
    opened = models.DateTimeField(auto_now=True)
    closed = models.DateTimeField(null=True, default=None, blank=True)
    expiration_date = models.DateField(_("Päättymispäivä"))
    scheme = models.ForeignKey(Scheme, related_name='participations')
    models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    upload_group = GenericRelation('attachtor.UploadGroup')

    objects = ParticipationQuerySet.as_manager()

    @property
    def attachments(self):
        if self.upload_group.count():
            return self.upload_group.first().upload_set
        return None

    def is_public(self):
        return self.status == self.STATUS_PUBLISHED

    def is_open(self):
        if self.status == self.STATUS_PUBLISHED:
            return not self.is_expired()
        return False

    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    def is_expired(self):
        return self.expiration_date < datetime.today().date()

    def expires_on_date(self):
        return self.expiration_date + timedelta(1)

    def is_conversation(self):
        return self.content_type == ContentType.objects. \
            get_by_natural_key('conversation', 'conversation')

    def is_survey(self):
        return self.content_type == ContentType.objects. \
            get_by_natural_key('survey', 'survey')

    def set_status_timestamp(self):
        ts_field = [s[1] for s in self.STATUSES if s[0] == self.status][0]
        setattr(self, ts_field, timezone.now())

    def __str__(self):
        return '%s' % self.title

    def get_absolute_url(self):
        if self.is_conversation():
            return reverse('content:participation:conversation_detail',
                           kwargs={'participation_detail_id': self.pk,
                                   'scheme_id': self.scheme_id})
        if self.is_survey():
            return reverse('content:participation:survey_detail',
                           kwargs={'participation_detail_id': self.pk,
                                   "scheme_id": self.scheme_id})

    def get_status_display(self):
        if self.is_expired():
            return _("Päättynyt")
        field = self._meta.get_field('status')
        return self._get_FIELD_display(field)

    def status_date(self):
        for status_id, status_time_field, status_verbal in self.STATUSES:
            if status_id == self.status:
                if self.status == ParticipationDetails.STATUS_PUBLISHED:
                    if self.is_open():
                        opened = date(self.opened, 'SHORT_DATE_FORMAT')
                        expires = date(self.expiration_date, 'SHORT_DATE_FORMAT')
                        return "{0} - {1}".format(opened, expires)
                    elif self.is_expired():
                        status_time_field = 'expiration_date'
                return date(getattr(self, status_time_field), 'SHORT_DATE_FORMAT')

    def label(self):
        if self.is_conversation():
            return {
                'open': _("Keskustelu on julkaistu"),
                'draft': _("Keskustelu on luonnos"),
                'expired': _("Keskustelu on päättynyt"),
                'open_it': _("Julkaise keskustelu"),
                'delete_it': _("Poista keskustelu"),
                'close_it': _("Päätä keskustelu"),
            }
        elif self.is_survey():
            return {
                'open': _("Kysely on avattu"),
                'draft': _("Kysely on luonnos"),
                'expired': _("Kysely on päättynyt"),
                'open_it': _("Julkaise kysely"),
                'delete_it': _("Poista kysely"),
                'close_it': _("Päätä kysely"),
            }

    def html_allowed(self):
        return True

    def participations_count(self):
        if self.is_conversation():
            return self.content_object.comments.public().count()
        elif self.is_survey():
            return self.content_object.submissions.count()

    def participations_count_exclude_owner(self):
        owner_pk_list = self.scheme.owner_ids
        if self.is_conversation():
            return self.content_object.comments.exclude(user_id__in=owner_pk_list).count()
        elif self.is_survey():
            return self.content_object.submissions \
                .exclude(submitter__user_id__in=owner_pk_list) \
                .count()

    def description_plaintext(self):
        # @attention: extra string conversion to get description for active language
        return strip_tags('%s' % self.description)

    def ready_to_publish(self):
        return self.status < ParticipationDetails.STATUS_PUBLISHED

    def ready_to_close(self):
        return not self.is_expired() and self.status > ParticipationDetails.STATUS_DRAFT

    def owner_ids(self):
        return self.scheme.owner_ids

    def last_participation_date(self):
        if self.is_conversation():
            return self.content_object.last_participation_date()
        else:
            last_submission = self.content_object.submissions.order_by('created').last()
            if last_submission:
                return last_submission.created.date()
        return datetime.min.date()

    def get_involved_user_ids(self):
        return self.content_object.get_involved_user_ids()

    class Meta:
        unique_together = (('content_type', 'object_id',),)
        ordering = ('-created', 'title',)
