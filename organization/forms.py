# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import ModelForm
from django.utils.translation import ugettext, ugettext_lazy as _
from content.models import SchemeOwner
from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn
from libs.fimunicipality.models import Municipality

from account.models import User
from organization.models import AdminSettings
from otakantaa.forms.fields import ModelMultipleChoiceField
from otakantaa.forms.forms import HiddenLabelMixIn
from otakantaa.forms.widgets import Select2Multiple, AutoSubmitButtonSelect
from otakantaa.utils import send_email
from .models import Organization


class OrganizationAdminsField(ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', User.objects.filter(is_active=True))
        kwargs.setdefault('label', ugettext("Valitse yhteyshenkilöt"))
        kwargs.setdefault('help_text', ugettext("Valitse organisaation yhteyshenkilöiden "
                                                "otakantaa.fi käyttäjätunnukset."))
        super(OrganizationAdminsField, self).__init__(*args, **kwargs)


class OrganizationAdminsMixin(object):
    def __init__(self, *args, **kwargs):
        org = kwargs.get('instance', None)
        if org is not None:
            kwargs.setdefault('initial', {})
            kwargs['initial']['admins'] = org.admins.all()
        super(OrganizationAdminsMixin, self).__init__(*args, **kwargs)

    @transaction.atomic()
    def save(self, commit=True):
        assert commit is True, "Must commit"
        instance = super(OrganizationAdminsMixin, self).save()

        unapproved = list(AdminSettings.objects.filter(
            organization=instance,
            approved=False).values_list('user_id', flat=True))
        instance.admins.clear()
        for u in self.cleaned_data['admins']:
            options = {'user': u, 'organization': instance}
            if u.pk in unapproved:
                options.update({'approved': False})
            AdminSettings.objects.create(**options)
        return instance


class CreateOrganizationForm(RedactorAttachtorFormMixIn, OrganizationAdminsMixin,
                             forms.ModelForm):
    type = forms.ChoiceField(choices=Organization.TYPE_CHOICES,
                             label=_("Organisaation tyyppi"))
    admins = OrganizationAdminsField()
    municipalities = ModelMultipleChoiceField(
        label=_("Valitse kunnat"),
        queryset=Municipality.objects.natural().active(),
        widget=Select2Multiple,
        required=False,
        help_text=_("Valitse kunta tai kunnat, joiden alueella organisaatio toimii.")
    )
    #terms_accepted = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        super(CreateOrganizationForm, self).__init__(*args, **kwargs)
        """
        self.fields["terms_accepted"].label = _(
            'Hyväksyn <a href="{}" target="_blank">käyttöehdot</a>.'.format(
                reverse("help:instruction_detail", args=[27])
            )
        )
        """

    def clean_admins(self):
        # The view should supply initial owners list containing the request.user,
        # make sure s/he is still on the list.
        admins = self.cleaned_data['admins']
        if self.initial['admins'][0] not in admins:
            raise forms.ValidationError(_("Et voi poistaa itseäsi yhteyshenkilöistä."))
        return admins

    class Meta:
        model = Organization
        fields = ('type', 'name', 'description', 'municipalities', 'admins', )


class EditOrganizationBaseForm(HiddenLabelMixIn, ModelForm):
    pass


class EditOrganizationNameForm(EditOrganizationBaseForm):

    class Meta:
        model = Organization
        fields = ('name', )


class EditOrganizationDescriptionForm(RedactorAttachtorFormMixIn,
                                      EditOrganizationBaseForm):

    class Meta:
        model = Organization
        fields = ('description', )


class EditOrganizationTypeForm(EditOrganizationBaseForm):
    type = forms.ChoiceField(choices=Organization.TYPE_CHOICES, label=_("Tyyppi"))

    class Meta:
        model = Organization
        fields = ("type", )


class EditOrganizationAdminsForm(OrganizationAdminsMixin, EditOrganizationBaseForm):
    admins = OrganizationAdminsField()

    def __init__(self, *args, **kwargs):
        super(EditOrganizationAdminsForm, self).__init__(*args, **kwargs)
        self.organization = kwargs["instance"]

    def send_email_notification(self):
        receivers = set(self.initial["admins"]) | set(self.cleaned_data["admins"])
        for receiver in receivers:
            send_email(
                _("Organisaation yhteyshenkilöitä on muutettu."),
                "organization/email/owner_change.txt",
                {"organization": self.organization},
                [receiver.settings.email],
                receiver.settings.language
            )
    """
    def save(self, commit=True):
        changed = self.has_changed()
        super(EditOrganizationAdminsForm, self).save(commit)
        if changed:
            self.send_email_notification()
    """
    def clean_admins(self):
        cleaned = self.cleaned_data['admins']

        # must not remove scheme owner organization admins
        for u in self.initial['admins']:
            if u not in cleaned:
                is_owner = SchemeOwner.objects.filter(
                    user_id=u.pk, organization_id=self.organization.pk).count()
                if is_owner:
                    raise forms.ValidationError(
                        _("{} on tämän organisaation yhteyshenkilönä ainakin yhdessä "
                          "hankkeessa. Hänet pitää ensin poistaa organisaation "
                          "hankkeista.".format(u)))
        return cleaned

    class Meta:
        model = Organization
        fields = ('admins', )


class EditOrganizationPictureForm(ModelForm):
    picture = forms.ImageField(label=_("Uusi kuva"), widget=forms.FileInput,
                               required=False)

    class Meta:
        model = Organization
        fields = ('picture', )


class OrganizationBaseSearchForm(ModelForm):

    NOT_ACTIVE = 'not active'
    SEARCH_TYPE_CHOICES = Organization.TYPE_CHOICES

    type_or_activity = forms.ChoiceField(
        choices=(("", _("Kaikki")), ) + SEARCH_TYPE_CHOICES,
        widget=AutoSubmitButtonSelect, required=False, label=False
    )

    words = forms.CharField(
        label=_("Hae organisaatio"), required=False,
        widget=forms.TextInput(attrs={'placeholder': _("Hae organisaatio")})
    )

    municipalities = ModelMultipleChoiceField(
        queryset=Municipality.objects.natural().active(),
        label=_("Valitse kunta"),
        required=False
    )

    def filtrate(self, qs):
        organization_type = self.cleaned_data["type_or_activity"]
        words = self.cleaned_data["words"]
        municipalities = self.cleaned_data["municipalities"]
        if organization_type:
            if organization_type == self.NOT_ACTIVE:
                qs = qs.filter(is_active=0)
            else:
                qs = qs.filter(type=organization_type).normal()
        else:
            qs = qs.filter(is_active=1)

        if words:
            qs = qs.filter(search_text__icontains=words)

        if municipalities:
            qs = qs.filter(
                municipalities__in=municipalities
            )

        return qs.order_by("-created")

    def save(self, commit=True):
        raise Exception("Ei sallittu.")

    class Meta:
        model = Organization
        fields = ('type_or_activity',)


class OrganizationSearchForm(OrganizationBaseSearchForm):
    pass


class OrganizationSearchFormAdmin(OrganizationBaseSearchForm):
    ADMIN_CHOICES = OrganizationBaseSearchForm.SEARCH_TYPE_CHOICES + \
              ((OrganizationBaseSearchForm.NOT_ACTIVE, _("Arkistoitu/ei aktiivinen")), )
    type_or_activity = forms.ChoiceField(
        choices=(("", _("Kaikki")), ) + ADMIN_CHOICES,
        widget=AutoSubmitButtonSelect, required=False, label=False
    )
