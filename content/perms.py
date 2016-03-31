# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _, ugettext

from libs.permitter import perms

from account import perms as account
from organization.models import AdminSettings
from otakantaa import perms as otakantaa

from .models import Scheme, SchemeOwner


class BaseSchemePermission(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.scheme = kwargs['obj']
        super(BaseSchemePermission, self).__init__(**kwargs)


class BaseParticipationPermission(otakantaa.BasePermission):
    def __init__(self, **kwargs):
        self.scheme = kwargs['obj'].scheme
        self.participation = kwargs['obj']
        super(BaseParticipationPermission, self).__init__(**kwargs)


class SchemeIsPublic(BaseSchemePermission):
    def is_authorized(self):
        return self.scheme.is_public()

    def get_unauthorized_url(self):
        return self.get_login_url()

    def get_unauthorized_message(self):
        if self.user.is_authenticated():
            msg = _("Hanke ei ole vielä julkinen.")
        else:
            msg = ' '.join((ugettext("Hanke ei ole vielä julkinen."),
                            ugettext("Kirjaudu sisään, jos olet hankkeen omistaja.")))
        return msg

    def get_login_url(self):
        if self.user.is_authenticated():
            return reverse('schemes')
        else:
            return super(SchemeIsPublic, self).get_login_url()


class OwnsSchemeCheck(BaseSchemePermission):
    def is_authorized(self):
        return self.request.user in self.scheme.owners.unique_users()


class OwnsSchemeCheckSloppy(BaseSchemePermission):
    def is_authorized(self):
        return self.request.user.pk in self.scheme.owners.values_list(
            'user_id', flat=True)


class SchemeIsPublished(BaseSchemePermission):
    def is_authorized(self):
        return self.scheme.status == Scheme.STATUS_PUBLISHED and \
            self.scheme.visibility == Scheme.VISIBILITY_PUBLIC


class SchemeIsClosed(BaseSchemePermission):
    def is_authorized(self):
        return self.scheme.status == Scheme.STATUS_CLOSED


class OwnsParticipation(BaseParticipationPermission):
    def is_authorized(self):
        return self.user.pk in self.participation.scheme.owner_ids


class ParticipationIsOpen(BaseParticipationPermission):
    def is_authorized(self):
        return self.participation.is_open()


class ParticipationIsPublic(BaseParticipationPermission):
    def is_authorized(self):
        return self.participation.is_public()


class SchemeNotYetPublished(BaseSchemePermission):
    unauthorized_message = _("Hanke on jo julkaistu.")

    def is_authorized(self):
        return self.scheme.status < self.scheme.STATUS_PUBLISHED

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})


class SchemeIsDraft(BaseSchemePermission):
    unauthorized_message = _("Hanke on vielä luonnos.")

    def is_authorized(self):
        return self.scheme.status == self.scheme.STATUS_DRAFT

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})


class ParticipationSchemeIsPublic(BaseParticipationPermission):
    def is_authorized(self):
        return SchemeIsPublic(request=self.request, obj=self.scheme).is_authorized()


class SchemeHasParticipations(BaseSchemePermission):
    def is_authorized(self):
        return True if self.scheme.participations.count() else False

    unauthorized_message = _("Hankkeen voi julkaista vasta kun siihen on liitetty kysely "
                             "tai keskustelu.")

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})


class SchemeHasPublishedParticipations(BaseSchemePermission):
    unauthorized_message = _("Hankkeessa ei ole yhtään julkaistua kyselyä tai "
                             "keskustelua.")

    def is_authorized(self):
        return self.scheme.participations \
            .filter(status__gte=Scheme.STATUS_PUBLISHED) \
            .exists()

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})


class SchemeParticipationsHaveParticipations(BaseSchemePermission):
    def is_authorized(self):
        return True if self.scheme.has_been_participated() else False


class ParticipationInteractionRegistered(BaseParticipationPermission):
    def is_authorized(self):
        return self.scheme.interaction == Scheme.INTERACTION_REGISTERED_USERS


class UserIsInvited(BaseSchemePermission):
    def __init__(self, **kwargs):
        self.scheme_owmner_pk = kwargs.get('scheme_owner_id', None)
        super(UserIsInvited, self).__init__(**kwargs)

    def is_authorized(self):
        if self.user.is_authenticated():
            self.unauthorized_message = _("Linkki on vanhentunut")
        else:
            self.unauthorized_message = _("Kirjaudu ensin sisään palveluun, "
                                          "jotta näet kutsun.")
        invited_user = SchemeOwner.objects.get(pk=self.scheme_owmner_pk).user
        return self.user == invited_user


class InvitationExists(BaseSchemePermission):
    def __init__(self, **kwargs):
        pk = kwargs.get('scheme_owner_id', None)
        self.scheme_owner = SchemeOwner.objects.filter(pk=pk, approved=False).first()
        super(InvitationExists, self).__init__(**kwargs)

    def get_login_url(self):
        return reverse('account:messages', kwargs={'user_id': self.user.pk})

    def is_authorized(self):
        if self.user.is_authenticated():
            self.unauthorized_message = _("Linkki on vanhentunut")
        else:
            self.unauthorized_message = _("Kirjaudu ensin sisään palveluun, "
                                          "jotta näet kutsun.")
        return True if self.scheme_owner is not None else False


class ParticipationIsDeletable(BaseParticipationPermission):
    def get_login_url(self):
        return self.participation.get_absolute_url()

    def is_authorized(self):
        return self.participation.participations_count_exclude_owner() == 0


class ParticipationIsPublishable(BaseParticipationPermission):
    def get_unauthorized_message(self):
        if self.participation.is_survey():
            return ugettext("Kyselyssä ei ole yhtään kysymystä.")
        return super(ParticipationIsPublishable, self).get_unauthorized_message()

    def get_login_url(self):
        return self.participation.get_absolute_url()

    def is_authorized(self):
        if self.participation.is_survey():
            return self.participation.content_object.elements.questions().exists()
        return True


class SchemeParticipationsArePublishable(BaseSchemePermission):
    def is_authorized(self):
        for participation in self.scheme.participations.surveys():
            if not participation.content_object.elements.questions().exists():
                self.unauthorized_message = ugettext(
                    "Kyselyssä '%(title)s' ei ole yhtään kysymystä."
                ) % participation.title
                return False
        return True

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})


class SchemeOrganizationAdminsAreApproved(BaseSchemePermission):
    def is_authorized(self):
        if self.scheme.is_organization_scheme:
            for o in self.scheme.owners.all():
                connection = AdminSettings.objects.filter(
                    user=o.user, organization=o.organization).first()
                if not connection:
                    return False
                if not connection.approved or not o.organization.is_active:
                    return False
        return True

    def get_login_url(self):
        return reverse('content:scheme_detail', kwargs={'scheme_id': self.scheme.pk})

    unauthorized_message = _("Hanketta ei voi vielä julkaista. Hankkeen omistajissa on "
                             "yhteyshenkilöitä tai organisaatioita, joita palvelun "
                             "ylläpitäjän ei ole hyväksynyt.")


OwnsScheme = perms.And(otakantaa.IsAuthenticated, OwnsSchemeCheck)
OwnsSchemeSloppy = perms.And(otakantaa.IsAuthenticated, OwnsSchemeCheckSloppy)

CanViewScheme = perms.Or(
    SchemeIsPublic,
    perms.And(
        otakantaa.IsAuthenticated,
        perms.Or(OwnsSchemeSloppy, otakantaa.IsModerator)
    )
)

CanEditScheme = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(OwnsScheme, otakantaa.IsModerator)
)

CanRevertSchemeToDraft = perms.And(
    SchemeIsPublished,
    perms.Or(
        perms.And(OwnsScheme, perms.Not(SchemeParticipationsHaveParticipations)),
        otakantaa.IsModerator
    )
)

CanDeleteScheme = perms.Or(
    perms.And(
        OwnsScheme,
        perms.Or(
            SchemeNotYetPublished,
            perms.Not(SchemeParticipationsHaveParticipations)
        )
    ),
    otakantaa.IsModerator
)

CanEditParticipation = perms.And(
    otakantaa.IsAuthenticated,
    perms.Or(OwnsParticipation, otakantaa.IsModerator)
)

CanViewParticipation = perms.Or(
    perms.And(
        ParticipationIsPublic,
        ParticipationSchemeIsPublic
    ),
    perms.And(
        otakantaa.IsAuthenticated,
        perms.Or(OwnsParticipation, otakantaa.IsModerator)
    )
)

CanPublishScheme = perms.And(CanEditScheme,
                             SchemeNotYetPublished,
                             SchemeHasParticipations,
                             SchemeParticipationsArePublishable,
                             SchemeOrganizationAdminsAreApproved)
CanSeeAllSchemes = perms.Or(account.OwnAccount, otakantaa.IsModerator)

NeedsLoginForParticipation = perms.And(
    ParticipationInteractionRegistered,
    perms.Not(otakantaa.IsAuthenticated)
)

CanParticipateParticipation = perms.Or(
    perms.Not(ParticipationInteractionRegistered),
    otakantaa.IsAuthenticated
)

CanAcceptInvitation = perms.And(
    InvitationExists,
    perms.Or(UserIsInvited, otakantaa.IsModerator)
)

CanCloseScheme = perms.And(
    SchemeIsPublished,
    perms.Or(OwnsScheme, otakantaa.IsModerator)
)

CanReopenScheme = perms.And(
    SchemeIsClosed,
    perms.Or(OwnsScheme, otakantaa.IsModerator)
)

CanDeleteParticipation = perms.And(
    ParticipationIsDeletable,
    OwnsParticipation
)

CanExportScheme = perms.And(
    perms.Not(SchemeIsDraft),
    perms.Or(OwnsScheme, otakantaa.IsModerator),
)

CanExportSchemePdf = CanExportScheme

CanExportSchemeExcel = perms.And(
    SchemeHasPublishedParticipations,
    CanExportScheme,
)

CanExportSchemeWord = CanExportScheme

CanPublishParticipation = ParticipationIsPublishable
