# coding=utf-8

from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from libs.multilingo.models.fields import MultilingualTextField
from mptt.models import MPTTModel, TreeForeignKey


@python_2_unicode_compatible
class Instruction(MPTTModel):
    title = MultilingualTextField(_("Otsikko"), max_length=255)
    description = MultilingualTextField(_("Sisältö"))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            db_index=True)
    order = models.PositiveIntegerField(default=1)


    TYPE_PRIVACY_POLICY = 'privacy-policy'
    TYPE_CONTACT_DETAILS = 'contact-details'
    TYPES = (
        (None, _("ei mitään")),
        (TYPE_PRIVACY_POLICY, _("rekisteriseloste")),
        (TYPE_CONTACT_DETAILS, _("yhteystiedot")),
    )
    TYPE_CHOICES = list(TYPES)
    connect_link_type = models.CharField(choices=TYPE_CHOICES, default=None, null=True,
                                         unique=True, max_length=50, blank=True)

    def __str__(self):
        return '%s' % self.title

    def save(self, *args, **kwargs):
        super(Instruction, self).save(*args, **kwargs)
        Instruction.objects.rebuild()

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        verbose_name = _("Ohje")
        verbose_name_plural = _("Ohjeet")
