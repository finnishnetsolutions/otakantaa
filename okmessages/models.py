# coding=utf-8

from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from polymorphic.polymorphic_model import PolymorphicModel
from account.models import User
from actions.models import ActionGeneratingModelMixin


@python_2_unicode_compatible
class Message(PolymorphicModel):
    sender = models.ForeignKey(User, null=True, related_name="sent_messages",
                               on_delete=models.SET_NULL, verbose_name=_("lähettäjä"))
    receivers = models.ManyToManyField(User, related_name="received_messages",
                                       verbose_name=_("vastaanottajat"),
                                       through="Delivery")
    subject = models.CharField(_("aihe"), max_length=255)
    message = models.CharField(_("viesti"), max_length=4000)
    sent = models.DateTimeField(default=timezone.now)

    # Which message this message is a reply to.
    reply_to = models.ForeignKey("self", null=True, on_delete=models.SET_NULL,
                                 related_name="replies")

    def __str__(self):
        return self.subject

    def is_feedback(self):
        return True if hasattr(self, 'feedback') else False

    def is_system_message(self):
        if not self.is_feedback() and not self.sender:
            return True
        return False

    def read_by_users(self):
        return [d.receiver for d in self.deliveries.deliveries_read()]

    def deleted_by_users(self):
        return [d.receiver for d in self.deliveries.deliveries_deleted()]

    class Meta:
        ordering = ("-sent",)
        verbose_name = _("viesti")
        verbose_name_plural = _("viestit")


@python_2_unicode_compatible
class Feedback(Message):
    name = models.CharField(_("nimi"), blank=True, max_length=50)
    email = models.EmailField(_("sähköposti"), blank=True)

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = _("palaute")
        verbose_name_plural = _("palautteet")


class DeliveryManager(models.Manager):

    def save_receivers(self, message=None, receivers=None):
        if not isinstance(message, Message):
            raise TypeError("Wrong type for message object")
        deliveries = []
        for user in receivers:
            obj = self.model(receiver=user, message=message)
            obj.save()
            deliveries.append(obj)
        return deliveries

    def user_in_receivers(self, user):
        return True if self.filter(receiver=user).count() else False

    def for_user(self, user):
        return self.get_queryset().filter(receiver=user)[0]

    def deliveries_read(self):
        return self.get_queryset().filter(read=True)

    def deliveries_deleted(self):
        return self.get_queryset().filter(deleted=True)


class Delivery(ActionGeneratingModelMixin, models.Model):
    message = models.ForeignKey(Message, related_name="deliveries")
    receiver = models.ForeignKey(User, related_name="message_deliveries")
    read = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    objects = DeliveryManager()

    def mark_as_read(self):
        self.read = True
        self.save()

    def mark_as_deleted(self):
        self.deleted = True
        self.save()

    def action_kwargs_on_create(self):
        return {'actor': self.message.sender}

    def fill_notification_recipients(self, action):
        action.add_notification_recipients(action.ROLE_CONTENT_OWNER, self.receiver)

    class Meta:
        unique_together = ('message', 'receiver', )

