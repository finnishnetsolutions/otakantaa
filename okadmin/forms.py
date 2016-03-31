# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.translation import ugettext as _

from bootstrap3_datetime.widgets import DateTimePicker
from libs.fimunicipality.models import Municipality

from otakantaa.forms.fields import ModelMultipleChoiceField
from otakantaa.forms.widgets import Select2
from account.models import User, UserSettings, GROUP_LABELS
from otakantaa.utils import send_email
from organization.models import Organization, AdminSettings


class GroupChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return dict(GROUP_LABELS).get(obj.name, obj.name)


class EditUserForm(forms.ModelForm):
    username = forms.CharField(label=_("Käyttäjänimi"), min_length=3, max_length=30)
    groups = GroupChoiceField(label=_("Käyttäjäryhmät"), queryset=Group.objects.all(),
                              required=False, help_text="")
    organizations = ModelMultipleChoiceField(queryset=Organization.objects.all(),
                                             label=_("Organisaatiot"), required=False)

    def __init__(self, *args, **kwargs):
        self.target_user = User.objects.get(pk=kwargs.pop("target_user"))
        is_admin = kwargs.pop("editor_is_admin")
        super(EditUserForm, self).__init__(*args, **kwargs)
        if not is_admin:
            del self.fields["groups"]
        self.initial['organizations'] = self.target_user.organizations.all()

    @transaction.atomic()
    def save(self, commit=True):
        changed = self.has_changed() and "groups" in self.changed_data
        super(EditUserForm, self).save(commit)

        unapproved = list(AdminSettings.objects.filter(
            user=self.target_user,
            approved=False).values_list('organization_id', flat=True))
        self.target_user.organizations.clear()
        for o in self.cleaned_data['organizations']:
            options = {'user': self.target_user, 'organization': o}
            if o.pk in unapproved:
                options.update({'approved': False})
            AdminSettings.objects.create(**options)

        if changed:
            send_email(
                _("Käyttöoikeuksiisi tehtiin muutoksia"),
                "okadmin/email/group_change.txt",
                {"target_user": self.target_user},
                [self.target_user.settings.email],
                self.target_user.settings.language
            )

    class Meta:
        model = User
        fields = ("username", "status", "groups")


class EditUserSettingsForm(forms.ModelForm):
    municipality = forms.ModelChoiceField(label=_("Kotikunta"),
                                          queryset=Municipality.objects.all(),
                                          widget=Select2, required=True,
                                          empty_label=_("Valitse"))

    class Meta:
        model = UserSettings
        fields = ("first_name", "last_name", "municipality", "email")
