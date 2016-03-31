# coding=utf-8

from __future__ import unicode_literals

from datetime import date

import logging

from django.db.models.query_utils import Q
from django.utils.translation import ugettext as _
from otakantaa.utils import send_email
from account.models import User

from .models import Scheme

logger = logging.getLogger(__package__)


def idle_schemes(reference_date, exact_date=False, **filter_kwargs):
    if not isinstance(reference_date, date):
        logger.info("Virheellinen pvm-ehto %d [idle_schemes].", reference_date)
        raise TypeError("Reference date should be a datetime.date object not %s"
                        % type(reference_date))

    idle_owners = User.objects.filter(is_active=True)

    if exact_date:
        idle_users = idle_owners.filter(last_login__startswith=reference_date)
        idle_owners = idle_owners.filter(Q(last_login__lt=reference_date) |
                                         Q(last_login__startswith=reference_date))
    else:
        idle_users = idle_owners = User.objects.exclude(last_login__gt=reference_date)
    schemes = Scheme.objects.filter(
        owners__user_id__in=idle_users.values_list('pk', flat=True),
        **filter_kwargs).distinct()
    # collect schemes where idle_users as owners - skip if scheme has an active user
    idle_list = []
    for s in schemes:
        not_idle = False
        for u in s.owners.unique_users():
            if u not in idle_owners:
                not_idle = True
                break

        if not_idle:
            continue

        if exact_date:
            if s.last_participation_date() == reference_date:
                idle_list.append(s)
        else:
            if s.last_participation_date() <= reference_date:
                idle_list.append(s)
    return idle_list


def archive_idle_schemes(archive_date):
    schemes = idle_schemes(
        archive_date,
        status=Scheme.STATUS_PUBLISHED,
        visibility=Scheme.VISIBILITY_PUBLIC
    )
    for scheme in schemes:
        scheme.visibility = Scheme.VISIBILITY_ARCHIVED
        scheme.status = Scheme.STATUS_CLOSED
        scheme.save()
        logger.info("Hanke %d arkistoitu.", scheme.pk)


def warn_of_archiving(warn_date, archive_date, test=False):
    """ Sends email to all schemes that are idle for longer than given date. """
    warn_days = (warn_date - archive_date).days
    idle_days = (date.today() - warn_date).days

    schemes = idle_schemes(
        warn_date,
        exact_date=True,
        status=Scheme.STATUS_PUBLISHED,
        visibility=Scheme.VISIBILITY_PUBLIC
    )

    for scheme in schemes:
        receivers = scheme.owners.unique_users()
        for receiver in receivers:
            send_email(
                _("Hankkeesi arkistoidaan %d päivän kuluttua.") % warn_days,
                "scheme/email/archive_warning.txt",
                {
                    "object": scheme,
                    "days_to_archive": warn_days,
                    "idle_days": idle_days
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Ilmoitus hankkeen %d arkistoinnista lähtetetty osoitteeseen %s.",
                        scheme.pk, receiver.settings.email)
