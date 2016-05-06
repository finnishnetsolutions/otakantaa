# coding=utf-8

from __future__ import unicode_literals

from itertools import chain
from operator import attrgetter

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.db.models.aggregates import Count, Sum
from django.db.models.query_utils import Q
from django.forms.models import ModelForm
from django.forms.widgets import RadioSelect
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils import timezone
from django.utils.safestring import mark_safe

from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn, FileUploadForm
from libs.attachtor.models.models import Upload
from libs.bs3extras.fields import LocalizedDateField
from libs.fimunicipality.models import Municipality
from libs.multilingo.forms.fields import MultiLingualField
from libs.multilingo.forms.widgets import SingleLanguageTextarea

from account.models import User
from conversation.models import Conversation
from organization.models import Organization
from otakantaa.forms.forms import HiddenLabelMixIn
from otakantaa.forms.widgets import Select2Multiple, AutoSubmitButtonSelect, \
    ButtonSelect, MultiLingualWidget, AutoSubmitHtmlButtonSelect
from otakantaa.forms.fields import ModelMultipleChoiceField, SaferFileField, \
    MultiEmailField
from survey.models import Survey, SurveyElement, SurveyQuestion
from tagging.models import Tag

from .models import Scheme, ParticipationDetails, SchemeOwner
from .fields import SchemeAdminOwnersMultiChoiceField, CustomMultiFileField


def get_admins_queryset(user=None, initial_owners=None):
    """
    :param user: user object
    :param initial_owners: schemeOwners qs
    :return: User.organization.through objects qs

    Get items for scheme organization owners select.
    Is used when creating or editing a scheme.
    """

    id_list = []
    # always return scheme owners
    if initial_owners:
        for o in initial_owners:
            id_list.append(
                User.organizations.through.objects.get(
                    user_id=o.user_id,
                    organization_id=o.organization_id
                ).pk
            )

    objects = User.organizations.through.objects

    if user:
        # if user is defined then also return users organizations that awaits activation
        objects = objects.filter(
            Q(pk__in=id_list) |
            Q(user_id=user.pk),
            Q(Q(organization__is_active=True) | Q(organization__activated__isnull=True))
        )
    else:
        # normally organizations have to be active and admins approved
        objects = objects.filter(
            Q(pk__in=id_list) |
            Q(Q(organization__is_active=True), Q(approved=True))
        )
    return objects.order_by('organization__name', 'user__username')


class CreateSchemeForm(forms.ModelForm):

    TARGET_TYPE_NATION = 0
    TARGET_TYPE_MUNICIPALITIES = 1

    WRITE_AS_USER = 0
    WRITE_AS_ORGANIZATION = 1

    lead_text = MultiLingualField(field_widget=SingleLanguageTextarea,
                                  widget=MultiLingualWidget, label=_("Tiivistelmä"),
                                  help_text=_("Kerro lyhyesti ja ymmärrettävästi mistä "
                                              "hankkeessa on kysymys."))

    write_as = forms.ChoiceField(
        label=_("Kirjoitetaanko hanke organisaationa vai käyttäjänä?"),
        widget=RadioSelect,
        choices=(
            (WRITE_AS_USER,          _("Kirjoita käyttäjänä")),
            (WRITE_AS_ORGANIZATION,  _("Kirjoita organisaationa"))
        ),
        initial=WRITE_AS_USER,
        help_text=_(
            "Olet yhteyshenkilönä vähintään yhdessä organisaatiossa, joten "
            "voit valita kirjoittaa hankkeen organisaationa tai tavallisena käyttäjänä."
        )
    )

    owners = ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_("Valitse hankkeen omistajien käyttäjätunnukset"),
        help_text=_("Valitse omistajien käyttäjätunnukset muiden käyttäjien "
                    "otakantaa.fi-käyttäjätunnuksista."), required=False
    )

    own_organizations = SchemeAdminOwnersMultiChoiceField(
        queryset=get_admins_queryset().none(),
        required=True,
        label=_("Oma organisaatio"),
        label_without_user=True,
    )

    invited_admins = SchemeAdminOwnersMultiChoiceField(
        queryset=get_admins_queryset().none(),
        required=False,
        label=_("Valitse muut organisaatiot"),
        help_text=_("Yhteyshenkilöille lähetetään kutsu hankkeen omistajaksi.")
    )

    tags = ModelMultipleChoiceField(
        label=_("Mitä aiheita hanke koskee?"), widget=Select2Multiple,
        queryset=Tag.objects.all(), required=True,
        help_text=_("Valitse hanketta kuvaavia aiheita"))

    target_type = forms.ChoiceField(
        label=_("Mitä kuntaa hanke koskee?"), widget=RadioSelect,
        initial=TARGET_TYPE_NATION,
        choices=(
            (TARGET_TYPE_NATION,        _("Hanke koskee koko Suomea")),
            (TARGET_TYPE_MUNICIPALITIES,  _("Valittuja kuntia")),
        ),
    )

    target_municipalities = ModelMultipleChoiceField(
        queryset=Municipality.objects.natural().active(),
        help_text=_("Valitse kunta tai kunnat, joihin hanke liittyy."),
        label='', required=False
    )

    def __init__(self, user, *args, **kwargs):
        super(CreateSchemeForm, self).__init__(*args, **kwargs)
        user_organizations = user.organizations.active_or_pending()
        self.user = user
        if user_organizations:
            self.fields['own_organizations'].queryset = get_admins_queryset(self.user)

            self.initial.update({
                'write_as': self.WRITE_AS_ORGANIZATION,
                'own_organizations': self.fields['own_organizations'].queryset[:1]})
            self.fields['invited_admins'].queryset = get_admins_queryset().exclude(
                user_id=self.user.pk
            )
        else:
            del self.fields['write_as']
            del self.fields['own_organizations']
            del self.fields['invited_admins']
            self.fields['owners'].required = True

    def clean_owners(self):
        """The view should supply initial owners list containing the request.user,
        make sure s/he is still on the list."""
        owners = self.cleaned_data['owners']
        write_as = self.cleaned_data.get('write_as', self.WRITE_AS_USER)

        if int(write_as) == self.WRITE_AS_USER:
            if self.initial['owners'][0] not in owners:
                raise forms.ValidationError(
                    _("Et voi poistaa itseäsi hankkeen omistajista."))
        return owners

    def clean(self):
        cleaned = super(CreateSchemeForm, self).clean()

        try:
            if int(cleaned['write_as']) == self.WRITE_AS_ORGANIZATION:
                cleaned['owners'] = []
            elif int(cleaned['write_as']) == self.WRITE_AS_USER:
                cleaned['target_organizations'] = []
        except KeyError:
            pass

        if not cleaned['target_municipalities'] and \
                int(cleaned['target_type']) == self.TARGET_TYPE_MUNICIPALITIES:
            self.add_error('target_municipalities', _("Tämä kenttä vaaditaan."))

        return cleaned

    def save_owners(self, commit=True):
        write_as = self.cleaned_data.get('write_as', self.WRITE_AS_USER)
        if int(write_as) == self.WRITE_AS_USER:
            owners = self.cleaned_data['owners']
        else:
            owners = chain(self.cleaned_data['own_organizations'],
                           self.cleaned_data['invited_admins'])
        new_objects = []
        for obj in owners:
            if obj.__class__ == User:
                conditions = {'scheme': self.instance, 'user': obj}
                user = obj
            else:
                user = obj.user
                conditions = {'scheme': self.instance, 'user': obj.user,
                              'organization': obj.organization}

            if user == self.user:
                conditions.update({'approved': True})

            new_obj = SchemeOwner(**conditions)
            if commit:
                new_obj.save()
            new_objects.append(new_obj)
        return new_objects

    class Meta:
        model = Scheme
        fields = ('title', 'lead_text', 'write_as', 'own_organizations',
                  'invited_admins', 'owners', 'tags', 'target_type',
                  'target_municipalities', 'interaction')
        widgets = {'interaction': RadioSelect, }


class EditContentBaseForm(HiddenLabelMixIn, ModelForm):
    pass


class EditSchemeTitleForm(EditContentBaseForm):
    class Meta:
        model = Scheme
        fields = ('title', )


class EditSchemeDescriptionForm(RedactorAttachtorFormMixIn, EditContentBaseForm):
    class Meta:
        model = Scheme
        fields = ('description', )


class EditSchemeLeadTextForm(EditContentBaseForm):
    lead_text = MultiLingualField(field_widget=SingleLanguageTextarea,
                                  widget=MultiLingualWidget,
                                  help_text=_("Kerro lyhyesti ja ymmärrettävästi mistä "
                                              "hankkeessa on kysymys."))

    class Meta:
        model = Scheme
        fields = ('lead_text', )


class EditSchemeSummaryForm(RedactorAttachtorFormMixIn, EditContentBaseForm):

    class Meta:
        model = Scheme
        fields = ('summary', )


class SaveOwnersFormMixin(object):

    def __init__(self):
        self.new_objects = None
        self.updated_objects = None
        self.deleted_objects = None

    def save_existing_objects(self, commit=True):
        for obj in self.deleted_objects:
            if commit:
                obj.delete()
        for obj in self.updated_objects:
            if commit:
                obj.save()
        return self.updated_objects

    def save_new_objects(self, commit=True):
        for obj in self.new_objects:
            if commit:
                obj.save()
        return self.new_objects


class EditSchemeOwnersBaseForm(EditContentBaseForm, SaveOwnersFormMixin):

    def __init__(self, user, *args, **kwargs):
        super(EditSchemeOwnersBaseForm, self).__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        obj = super(EditSchemeOwnersBaseForm, self).save(commit)
        self.instance = obj
        self.save_owners(commit)
        return obj

    def save_owners(self, commit=True):
        self.new_objects = []
        self.updated_objects = []
        for obj in self.cleaned_data['owners']:
            conditions = self.build_conditions(obj)

            try:
                existing_owner = SchemeOwner.objects.get(**conditions)
            except SchemeOwner.DoesNotExist:
                existing_owner = None

            if conditions['user'] == self.user:
                conditions.update({'approved': True})

            if not existing_owner:
                self.new_objects.append(SchemeOwner(**conditions))
            else:
                self.updated_objects.append(existing_owner)

        self.deleted_objects = self.instance.owners.exclude(
            pk__in=[x.pk for x in self.updated_objects])

        return self.save_existing_objects(commit) + self.save_new_objects(commit)

    def build_conditions(self, obj):
        user = obj if obj.__class__ == User else obj.user
        return {'scheme': self.instance, 'user': user}


class EditSchemeOwnersForm(EditSchemeOwnersBaseForm):
    owners = SchemeAdminOwnersMultiChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_("Omistajat"),
        help_text=_("Valitse hankkeen omistajien käyttäjätunnukset."),
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super(EditSchemeOwnersForm, self).__init__(user, *args, **kwargs)
        self.initial = {
            'owners': self.instance.owners.all()
        }
        self.fields['owners'].widget.instance = self.instance

    def get_initial_owners_user_list(self):
        initial_users = []
        for o in self.initial['owners']:
            initial_users.append(o.user)
        return initial_users

    def clean_owners(self):
        """The view should supply initial owners list containing the request.user,
        make sure s/he is still on the list."""
        owners = self.cleaned_data['owners']

        if not self.user.is_moderator or self.user in self.get_initial_owners_user_list():
            if self.user.pk not in owners.values_list('pk', flat=True):
                raise forms.ValidationError(_("Et voi poistaa itseäsi hankkeen omistajista."))
        return owners

    def has_changed(self):
        initial_users = self.get_initial_owners_user_list()
        cleaned_users = []
        for o in self.cleaned_data['owners']:
            cleaned_users.append(o)
        return sorted(initial_users) != sorted(cleaned_users)

    class Meta:
        model = Scheme
        fields = ('owners', )


class EditSchemeAdminOwnersForm(EditSchemeOwnersBaseForm):

    def __init__(self, user, *args, **kwargs):
        super(EditSchemeAdminOwnersForm, self).__init__(user, *args, **kwargs)
        self.initial = {'owners': self.instance.owners.all()}
        self.fields['owners'].widget.instance = self.instance
        self.fields['owners'].queryset = get_admins_queryset(
            initial_owners=self.instance.owners.all())

    owners = SchemeAdminOwnersMultiChoiceField(
        required=False,
        queryset=get_admins_queryset().none(),
        label=_("Omistajat"),
        help_text=_("Valitse hankkeen omistajat organisaatioiden yhteyshenkilöistä."),
    )

    def clean_owners(self):
        self_in_owners = False
        for obj in self.cleaned_data['owners']:
            if self.user == obj.user:
                self_in_owners = True
                break

        initial_users = []
        for o in self.initial['owners']:
            initial_users.append(o.user)

        if not self.user.is_moderator or self.user in initial_users:
            if not self_in_owners:
                raise forms.ValidationError(
                    _("Et voi poistaa itseäsi hankkeen omistajista."))
        return self.cleaned_data['owners']

    def build_conditions(self, obj):
        conditions = super(EditSchemeAdminOwnersForm, self).build_conditions(obj)
        conditions.update({'organization': obj.organization})
        return conditions

    def has_changed(self):
        initial_users = []
        for o in self.initial['owners']:
            initial_users.append("{}:{}".format(o.user_id, o.organization_id))

        cleaned_users = []
        for o in self.cleaned_data['owners']:
            cleaned_users.append("{}:{}".format(o.user_id, o.organization_id))
        return sorted(cleaned_users) != sorted(initial_users)

    class Meta:
        model = Scheme
        fields = ('owners', )


class AcceptOwnerInvitationForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AcceptOwnerInvitationForm, self).__init__(*args, **kwargs)
        self.initial = {'approved': True}

    class Meta:
        model = SchemeOwner
        fields = ('approved', )
        widgets = {'approved': forms.RadioSelect}


class EditSchemeTagsForm(EditContentBaseForm):
    class Meta:
        model = Scheme
        fields = ('tags', )
        widgets = {'tags': Select2Multiple}


class EditSchemeMunicipalitiesForm(EditContentBaseForm):

    def __init__(self, *args, **kwargs):
        super(EditSchemeMunicipalitiesForm, self).__init__(*args, **kwargs)

        # if len = 0 then "koko suomi"
        if len(self.initial['target_municipalities']) == 0:
            self.fields['target_municipalities'].required = False

    class Meta:
        model = Scheme
        fields = ('target_municipalities', )
        widgets = {'target_municipalities': Select2Multiple}


class EditSchemePictureForm(ModelForm):
    picture = forms.ImageField(label=_("Uusi kuva"), widget=forms.FileInput,
                               required=False,
                               help_text=_("Kuva skaalataan 710 pikseliä leveäksi. "
                                           "Parhaan lopputuloksen saat tallentamalla "
                                           "vähintään 710 pikseliä leveän kuvan."))

    picture_alt_text = forms.CharField(label=_("Kuvan tekstimuotoinen kuvaus"),
                                       required=False)

    class Meta:
        model = Scheme
        fields = ('picture', 'picture_alt_text')


class AttachmentUploadForm(FileUploadForm):
    file = SaferFileField()

    def __init__(self, *args, **kwargs):
        self.uploader = kwargs.pop('uploader')
        self.upload_group = kwargs.pop('upload_group')
        super(FileUploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(AttachmentUploadForm, self).clean()
        limits = settings.ATTACHMENTS
        if 'file' in cleaned:
            file = cleaned['file']
            if file.size > limits['max_size']:
                raise forms.ValidationError(ugettext("Tiedosto ylittää kokorajoituksen."))
            if self.upload_group is not None:
                obj_totals = self.upload_group.upload_set.aggregate(
                    count=Count('id'), total_size=Sum('size')
                )
                if (obj_totals['count'] or 0) >= limits['max_attachments_per_object']:
                    raise forms.ValidationError(
                        ugettext("Liian monta liitetiedostoa lisätty.")
                    )
            uploader_total = Upload.objects.filter(
                uploader=self.uploader,
                created__gte=timezone.now() - limits['max_size_per_uploader_timeframe']
            ).aggregate(size=Sum('size'))
            if (uploader_total['size'] or 0) + file.size > \
                    limits['max_size_per_uploader']:
                raise forms.ValidationError(
                    ugettext("Olet lisännyt liian monta liitetiedostoa. "
                             "Yritä myöhemmin uudestaan.")
                )
        return cleaned


class UploadMultipleAttachmentsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UploadMultipleAttachmentsForm, self).__init__(*args, **kwargs)

    files = CustomMultiFileField(help_text=_("Voit valita monta liitettä kerralla."),
                                 label='', max_num=10,
                                 max_file_size=settings.ATTACHMENTS['max_size'])

    def save(self, commit=True):
        group = self.instance
        for item in self.cleaned_data['files']:
            upload = Upload.objects.create(file=item, group=group, original_name=item,
                                           uploader=self.user, size=item.size)
            upload.save()
        return group

    class Meta:
        model = Upload
        fields = ('files', )


class EditParticipationTitleForm(EditContentBaseForm):
    class Meta:
        model = ParticipationDetails
        fields = ('title', )


class EditParticipationDescriptionForm(RedactorAttachtorFormMixIn, EditContentBaseForm):

    class Meta:
        model = ParticipationDetails
        fields = ('description', )


class EditParticipationExpirationDateForm(EditContentBaseForm):
    expiration_date = LocalizedDateField(label=_("Päättymisaika"))

    class Meta:
        model = ParticipationDetails
        fields = ('expiration_date', )


class CreateParticipationForm(RedactorAttachtorFormMixIn, forms.ModelForm):

    expiration_date = LocalizedDateField(label=_("Päättymisaika"))

    class Meta:
        model = ParticipationDetails
        fields = ('scheme', 'title', 'description', 'expiration_date', )
        widgets = {'scheme': forms.HiddenInput}


class SchemeSearchForm(forms.Form):
    STATUS_CHOICES = (
        ("", _("Kaikki")),
        (Scheme.STATUS_PUBLISHED, _("Avoimet")),
        (Scheme.STATUS_CLOSED, _("Päättyneet")),
    )

    PARTICIPATIONS_CONVERSATION = "conversation"
    PARTICIPATIONS_SURVEY = "survey"
    PARTICIPATIONS_CHOICES = (
        ("", _("Kaikki")),
        (PARTICIPATIONS_CONVERSATION, _("Keskustelu")),
        (PARTICIPATIONS_SURVEY, _("Kysely")),
    )

    OWNER_ORGANIZATION = "organization"
    OWNER_OTHER = "other"
    OWNER_CHOICES = (
        ("", _("Kaikki")),
        (OWNER_ORGANIZATION, _("Organisaatiot")),
        (OWNER_OTHER, _("Muut")),
    )

    DISPLAY_TYPE_BOXES = "boxes"
    DISPLAY_TYPE_LIST = "list"
    DISPLAY_TYPE_CHOICES = (
        (DISPLAY_TYPE_BOXES, mark_safe('<span class="glyphicon glyphicon-th">'
                                       '<span class="sr-only">{}</span>'
                                       '</span>').format(_("Ruudukko"))),
        (DISPLAY_TYPE_LIST, mark_safe('<span class="glyphicon glyphicon-list">'
                                      '<span class="sr-only">{}</span>'
                                      '</span>').format(_("Lista"))),
    )
    DEFAULT_DISPLAY_TYPE = DISPLAY_TYPE_BOXES

    SORTING_NEWEST = "newest"
    SORTING_POPULARITY = "popularity"
    SORTING_HOTTEST = "hotness"
    SORTING_CHOICES = (
        (SORTING_NEWEST, _("Uusimmat")),
        (SORTING_POPULARITY, _("Suosituimmat")),
        (SORTING_HOTTEST, _("Kuumimmat nyt")),
    )

    text = forms.CharField(
        label=False, required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Hae hankkeita")})
    )

    text_with_button = forms.CharField(
        label=False, required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Hae hankkeita")})
    )
    municipality = ModelMultipleChoiceField(
        queryset=Municipality.objects.natural().active(),
        label=_("Paikkakunta"),
        required=False
    )

    tags = ModelMultipleChoiceField(label=_("Aihe"), widget=Select2Multiple,
                                    queryset=Tag.objects.all(), required=False)

    organization = ModelMultipleChoiceField(queryset=Organization.objects.normal(),
                                            label=_("Valitse organisaatio"),
                                            required=False)
    status = forms.ChoiceField(label=_("Tila"), choices=STATUS_CHOICES,
                               required=False, widget=ButtonSelect)
    participations = forms.ChoiceField(label=_("Osallistumiset"),
                                       choices=PARTICIPATIONS_CHOICES, required=False,
                                       widget=ButtonSelect)
    owner_type = forms.ChoiceField(label=_("Hankkeen perustaja"), choices=OWNER_CHOICES,
                                   required=False, widget=ButtonSelect)

    extended_search = forms.BooleanField(required=False)
    sorting = forms.ChoiceField(choices=SORTING_CHOICES, required=False,
                                widget=AutoSubmitButtonSelect, label=False)
    display_type = forms.ChoiceField(choices=DISPLAY_TYPE_CHOICES, required=False,
                                     widget=AutoSubmitHtmlButtonSelect, label=False)

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop("user")
        super(SchemeSearchForm, self).__init__(*args, **kwargs)

    def filtrate(self, qs):
        # Filtering.
        extended_search = self.cleaned_data.get("extended_search")
        text = self.cleaned_data.get("text") or self.cleaned_data.get("text_with_button")

        if text:
            qs = qs.filter(search_text__icontains=text)

        if extended_search:
            # Extended search.
            municipality = self.cleaned_data.get("municipality")
            organization = self.cleaned_data.get("organization")
            status = self.cleaned_data.get("status")
            tags = self.cleaned_data.get("tags")
            owner_type = self.cleaned_data.get("owner_type")
            participations = self.cleaned_data.get("participations")

            if municipality:
                qs = qs.filter(target_municipalities__in=municipality)

            if organization:
                qs = qs.filter(owners__organization__in=organization,
                               owners__approved=True)

            if status:
                qs = qs.filter(status=status)

            if tags:
                qs = qs.filter(tags__in=tags)

            if owner_type:
                if owner_type == self.OWNER_ORGANIZATION:
                    qs = qs.filter(owners__organization_id__gte=0)
                elif owner_type == self.OWNER_OTHER:
                    qs = qs.exclude(owners__organization_id__gte=0)

            if participations:
                pd_kwargs = {'participations__status':
                             ParticipationDetails.STATUS_PUBLISHED}
                if participations == self.PARTICIPATIONS_CONVERSATION:
                    ct = ContentType.objects.get_for_model(Conversation)
                elif participations == self.PARTICIPATIONS_SURVEY:
                    ct = ContentType.objects.get_for_model(Survey)
                pd_kwargs.update({'participations__content_type': ct})
                qs = qs.filter(**pd_kwargs)
            qs = qs.distinct()

        # Sorting.
        sorting = self.cleaned_data.get("sorting")
        if sorting == self.SORTING_NEWEST:
            qs = qs.order_by("-published")
        elif sorting in [self.SORTING_POPULARITY, self.SORTING_HOTTEST]:
            qs = sorted(qs, key=attrgetter(sorting), reverse=True)

        return qs


class BaseExportForm(forms.Form):
    def add_emails_field(self):
        self.fields["emails"] = MultiEmailField(
            required=False,
            label=_("Lähetä sähköpostilla"),
            help_text=_("Erottele sähköpostiosoitteet välilyönnillä. "
                        "Jätä tyhjäksi ladataksesi tiedosto.")
        )


class ExportTextForm(BaseExportForm):
    """
    Used for PDF-export. Possibly usable for Word-export in the future.
    If not, change name to ExportPdfForm.
    """
    SCHEME_INFORMATION_CHOICES = (
        (True, _("Kyllä")),
        (False, _("Ei")),
    )
    scheme_information = forms.BooleanField(
        required=False, label=_("Hankkeen tiedot"), initial=True,
        widget=forms.RadioSelect(choices=SCHEME_INFORMATION_CHOICES),
    )

    def __init__(self, scheme_id, *args, **kwargs):
        super(ExportTextForm, self).__init__(*args, **kwargs)
        details_queryset = ParticipationDetails.objects.filter(
            scheme_id=scheme_id,
            status__gte=ParticipationDetails.STATUS_PUBLISHED,
        )
        conversations_queryset = details_queryset.conversations()
        if conversations_queryset.exists():
            self.fields["conversations"] = forms.ModelMultipleChoiceField(
                queryset=conversations_queryset,
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=_("Valitse keskustelut"),
            )
        surveys_queryset = details_queryset.surveys()
        if surveys_queryset.exists():
            self.fields["surveys"] = forms.ModelMultipleChoiceField(
                queryset=surveys_queryset,
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label=_("Valitse kyselyt"),
            )
        self.add_emails_field()

    def clean(self):
        cleaned_data = super(ExportTextForm, self).clean()
        scheme_information = cleaned_data.get("scheme_information")
        conversations = cleaned_data.get("conversations")
        surveys = cleaned_data.get("surveys")

        if scheme_information is False and not conversations and not surveys:
            raise forms.ValidationError(
                ugettext("Et valinnut mitään tietoja ladattavaksi.")
            )


class ExportExcelForm(BaseExportForm):
    def __init__(self, scheme_id, *args, **kwargs):
        super(ExportExcelForm, self).__init__(*args, **kwargs)
        details_queryset = ParticipationDetails.objects.filter(
            scheme_id=scheme_id,
            status__gte=ParticipationDetails.STATUS_PUBLISHED,
        )
        conversation_queryset = details_queryset.conversations()
        if conversation_queryset.exists():
            self.fields["conversation"] = forms.ModelChoiceField(
                label=_("Keskustelut"),
                queryset=conversation_queryset,
                widget=forms.RadioSelect,
                required=False,
                empty_label=None,
            )
        survey_queryset = details_queryset.surveys().prefetch_related(
            Prefetch("content_object__elements",
                     queryset=SurveyElement.objects.instance_of(SurveyQuestion),
                     to_attr="questions"),
        )
        if survey_queryset.exists():
            self.fields["survey"] = forms.ModelChoiceField(
                label=_("Kyselyt"),
                queryset=survey_queryset,
                widget=forms.RadioSelect,
                required=False,
                empty_label=None,
            )
        self.add_emails_field()

    def clean(self):
        cleaned_data = super(ExportExcelForm, self).clean()
        conversation = cleaned_data.get("conversation")
        survey = cleaned_data.get("survey")

        if conversation and survey:
            error_message = ugettext("Valitse vain joko keskustelu tai kysely.")
            self.add_error("conversation", error_message)
            self.add_error("survey", error_message)

        if not (conversation or survey):
            error_message = ugettext("Valitse keskustelu tai kysely.")
            self.add_error("conversation", error_message)
            self.add_error("survey", error_message)

    def get_participation_details(self):
        if self.cleaned_data.get("conversation"):
            return self.cleaned_data["conversation"]
        elif self.cleaned_data.get("survey"):
            return self.cleaned_data["survey"]

    def get_participation(self):
        return self.get_participation_details().content_object


class CloseSchemeForm(RedactorAttachtorFormMixIn, forms.ModelForm):

    class Meta:
        model = Scheme
        fields = ('summary', )
