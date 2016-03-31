# coding=utf-8

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from account.models import User, MODERATOR_GROUP_NAMES

from .models import Delivery, Message


def send_message(subject=None, message=None, receivers=None, sender=None):

    # handles user objects or a list of user objects
    if isinstance(receivers, User):
        receivers = [receivers, ]

    if not type(receivers) is list:
        raise TypeError("Wrong type for receivers list")

    if not len(receivers):
        return None

    msg = Message.objects.create(
        sender=sender,
        subject=subject,
        message=message,
    )
    Delivery.objects.save_receivers(msg, receivers)
    return msg


def send_message_to_moderators(subject=None, message=None, sender=None):
    moderators = list(User.objects.filter(groups__name__in=MODERATOR_GROUP_NAMES))
    send_message(subject, message, moderators, sender)



