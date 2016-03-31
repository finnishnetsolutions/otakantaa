# coding=utf-8

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import timedelta
from urllib2 import urlopen
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.db.models.query_utils import Q
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import ugettext as _, ugettext, string_concat
from django.views import generic
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from libs.ajaxy.responses import AjaxyInlineRedirectResponse
from libs.djcontrib.views.generic import MultiModelFormView

from content.models import Scheme
from content.perms import CanSeeAllSchemes, CanEditScheme
from conversation.models import Conversation
from okmessages.models import Message, Delivery
from okmessages.utils import send_message_to_moderators
from organization.models import Organization, AdminSettings
from otakantaa.perms import IsAuthenticated
from otakantaa.utils import send_email
from survey.models import SurveySubmission, Survey

from . import forms
from .forms import NotificationOptionsForm
from .models import User


# Get an instance of a logger
logger = logging.getLogger(__name__)


class SignupChoicesView(TemplateView):
    template_name = 'account/authentication/signup_choices.html'


class SignupView(MultiModelFormView):
    template_name = 'account/authentication/signup.html'
    form_classes = (
        ('user', forms.UserForm),
        ('usersettings', forms.UserSignUpForm),
    )
    confirmation_email_template = 'account/email/confirm_signup.txt'

    facebook = False

    def form_invalid(self):
        messages.error(self.request, _("Täytä kaikki pakolliset kentät."))
        return super(SignupView, self).form_invalid()

    @transaction.atomic()
    def form_valid(self):
        self.save_forms()
        self.connect_to_organization(self.forms['usersettings'].cleaned_data)
        if self.facebook:
            self.request.session["new_user"] = self.objects["user"]
            return redirect("social:complete", "facebook")
        else:
            return redirect("account:activate")

    def connect_to_organization(self, data):
        if data['connect_to_organization']:
            if data['existing_organization']:

                AdminSettings.objects.create(
                    organization=data['existing_organization'],
                    user=self.objects['user'],
                    approved=False
                )

                messages.success(self.request,
                                 _("Organisaatio kytketään käyttäjätiliisi kun olet "
                                   "vahvistanut rekisteröitymisesi. Voit luoda hankkeita "
                                   "organisaation edustajana, mutta niiden julkaiseminen "
                                   "onnistuu vasta palvelun ylläpitäjän hyväksyttyä "
                                   "käyttäjäsi organisaation yhteyshenkilöksi."))

                send_message_to_moderators(
                    string_concat(ugettext("Organisaation edustaja"),
                                  " (", ugettext("rekisteröityminen"), ")"),
                    render_to_string('okmessages/messages/connect_to_organization.txt', {
                        'user': self.objects['user'],
                        'u_url': self.objects['user'].get_absolute_url(),
                        'organization': data['existing_organization'],
                        'o_url': data['existing_organization'].get_absolute_url()
                    })
                )

            elif data['new_organization']:
                # create a new inactive organization and add user as admin
                org = Organization.objects.create(
                    name=data['new_organization'],
                    type=Organization.TYPE_OTHER,
                    description="Rekisteröitymisen yhteydessä luotu organisaatio. Lisää "
                                "organisaatiolle oikea tyyppi sekä kuvaus.",
                )
                AdminSettings.objects.create(
                    organization=org,
                    user=self.objects['user'],
                )

                send_message_to_moderators(
                    string_concat(ugettext("Organisaation edustaja"),
                                  " (", ugettext("rekisteröityminen"), ")"),
                    render_to_string('okmessages/messages/new_organization.txt', {
                        'organization': org,
                        'o_url': org.get_absolute_url()
                    })
                )

    def presave_usersettings(self, obj):
        """Link ``UserSettings`` to ``User`` before attempting to save."""
        obj.user = self.objects['user']

    def postsave(self):
        """``User`` and ``UserSettings`` have been saved, send the activation message."""
        user = self.objects['user']
        self.send_confirmation_email(user)

        # Save the profile picture from Facebook, if chosen to.
        if self.facebook and self.request.POST["facebook_pic"] == "yes":
            facebook_id = self.request.session.get("fb_id")
            url = "http://graph.facebook.com/{0}/picture?type=large".format(facebook_id)
            picture = urlopen(url).read()
            user.settings.picture.save(
                user.username + "-social.jpg",
                ContentFile(picture),
                save=True
            )

    def send_confirmation_email(self, user):
        activation_link = settings.BASE_URL + reverse(
            'account:confirm_email', kwargs={
                'token': forms.EmailConfirmationForm.create_token(user)
            }
        )
        send_email(
            _("Vahvista sähköpostiosoitteesi."),
            self.confirmation_email_template,
            {'activation_link': activation_link},
            [user.settings.email],
            user.settings.language
        )

    def get_usersettings_initial(self):
        initials = {'language': self.request.LANGUAGE_CODE}
        if self.facebook:
            initials.update({
                "email": self.request.session.get("fb_email"),
                "first_name": self.request.session.get("fb_first_name"),
                "last_name": self.request.session.get("fb_last_name"),
            })
        else:
            try:
                del self.request.session["fb_email"]
                del self.request.session["fb_first_name"]
                del self.request.session["fb_last_name"]
            except KeyError:
                pass
        return initials

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context["facebook"] = self.facebook
        context["facebook_id"] = self.request.session.get("fb_id")
        return context


def send_account_activated_email(user):
        send_email(
            _("Käyttäjätili avattu."),
            'account/email/account_created.txt',
            {'user': user},
            [user.settings.email],
            user.settings.language
        )


class EmailConfirmationView(generic.FormView):
    form_class = forms.EmailConfirmationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(data=kwargs)

        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            user.save()
            send_account_activated_email(user)
            login(request, user)

            return TemplateResponse(
                request,
                'account/authentication/signup_activated.html', {
                    'object': user,
                })
        else:
            return TemplateResponse(
                request,
                'account/authentication/email_confirmation_failed.html',
                {'form': form})


class LogoutView(generic.RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        logout(self.request)
        messages.success(
            self.request,
            ' '.join([
                _("Sinut on kirjattu ulos palvelusta."),
                _("Jos olet käyttänyt Facebook-kirjautumista, "
                  "muista kirjautua ulos myös Facebookista.")
            ])
        )
        return reverse("schemes")


class LoginView(generic.FormView):
    form_class = forms.LoginForm
    template_name = 'account/authentication/login.html'
    redirect_next = ''
    
    def form_valid(self, form):
        user = form.get_user()
        last_login = user.last_login
        login(self.request, user)
        if (last_login - user.joined) < timedelta(seconds=3):
            messages.success(self.request, _("Tervetuloa otakantaa.fi-palveluun!"))
        else:
            login_date = timezone.localtime(last_login)
            messages.success(self.request, _("Tervetuloa! Kirjauduit sisään viimeksi %s.")
                             % date_format(login_date, 'SHORT_DATETIME_FORMAT'))
        logger.info('User %s logged in. IP: %s', user.username,
                    self.request.META['REMOTE_ADDR'])

        if 'next' in self.request.GET:
            return HttpResponseRedirect(self.request.GET['next'])
        return redirect(reverse('account:profile', kwargs={'user_id': user.pk}))

    def form_invalid(self, form):
        logger.info('Invalid login try for username %s. IP %s',
                    form.cleaned_data['username'], self.request.META['REMOTE_ADDR'])
        return super(LoginView, self).form_invalid(form)


class InlineUpdateView(UpdateView):
    def form_valid(self, form):
        super(InlineUpdateView, self).form_valid(form)
        return AjaxyInlineRedirectResponse(self.get_success_url())


class ExistingUserMixIn(object):
    def get_object(self, queryset=None):
        return self.kwargs['obj']


class UserSettingsMixIn(object):
    def get_object(self, queryset=None):
        return self.kwargs['obj'].settings


class EditProfilePictureView(UserSettingsMixIn, InlineUpdateView):
    template_name = 'account/user_settings_base_form.html'
    form_class = forms.EditProfilePictureForm

    def get_success_url(self):
        return reverse('account:profile_picture',
                       kwargs={'user_id': self.kwargs['obj'].pk})


class ProfilePictureView(ExistingUserMixIn, DetailView):
    template_name = 'account/user_settings_picture.html'


class DeleteProfilePictureView(View):
    def delete(self, request, **kwargs):
        obj = get_object_or_404(User, pk=kwargs['user_id'])
        obj.settings.picture.delete()
        return AjaxyInlineRedirectResponse(reverse('account:profile_picture',
                                                   kwargs={'user_id': obj.pk}))

    def post(self, request, **kwargs):
        return self.delete(request, **kwargs)


class UserProfileSchemeMixInView(object):
    def get_schemes(self):
        user = self.get_object()
        schemes = user.owned_schemes.real().schemes()
        r_user = self.request.user
        if not CanSeeAllSchemes(request=self.request, obj=user).is_authorized():
            if IsAuthenticated(request=self.request).is_authorized():
                r_user_scheme_ids = r_user.schemes.all().values_list('pk', flat=True)
                schemes = schemes.filter(
                    Q(pk__in=r_user_scheme_ids) |
                    Q(visibility=Scheme.VISIBILITY_PUBLIC)
                )
            else:
                schemes = schemes.filter(visibility=Scheme.VISIBILITY_PUBLIC)
        return schemes.distinct().order_by('-pk')


class UserProfileView(generic.DetailView, UserProfileSchemeMixInView):
    pk_url_kwarg = 'user_id'
    template_name = 'account/user_profile.html'
    form_class = forms.UserProfileSchemeListForm

    def get_object(self, queryset=None):
        return self.kwargs['obj']

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context['schemes'] = self.get_schemes()
        context['form'] = self.form_class
        context['admin_in_set'] = AdminSettings.objects.filter(
            user=self.get_object())

        return context


class UserProfileSchemeListView(generic.TemplateView, UserProfileSchemeMixInView):
    template_name = 'account/user_profile_scheme_list.html'

    def get_object(self, **kwargs):
        return User.objects.get(pk=self.kwargs['user_id'])

    def get_context_data(self, **kwargs):
        context = super(UserProfileSchemeListView, self).get_context_data(**kwargs)
        context['schemes'] = self.get_schemes()
        context['ct_natural_key'] = self.request.GET['ct_natural_key']
        context['object'] = self.get_object()
        context['form'] = forms.UserProfileSchemeListForm(
            initial={'ct_natural_key': context['ct_natural_key']}
        )

        if not re.match('^([a-z])+\.([a-z])+$', context['ct_natural_key']):
            context['obj_list'] = self.get_non_favorite_schemes(context['ct_natural_key'])
            context['ct_natural_key'] = None
        return context

    def get_commented_schemes_id_list(self):
        conversations_id_list = Conversation.objects.filter(
            comments__user_id=self.get_object().pk).values_list('pk', flat=True).\
            distinct()
        ct = ContentType.objects.get_for_model(Conversation)
        return Scheme.objects.filter(
            participations__content_type=ct,
            participations__object_id__in=conversations_id_list).\
            values_list('pk', flat=True)

    def get_voted_schemes_id_list(self):
        conversations_id_list = Conversation.objects.filter(
            comments__votes__voter__user_id=self.get_object().pk).\
            values_list('pk', flat=True).distinct()
        ct = ContentType.objects.get_for_model(Conversation)
        return Scheme.objects.filter(
            participations__content_type=ct,
            participations__object_id__in=conversations_id_list).\
            values_list('pk', flat=True)

    def get_answered_surveys_schemes_id_list(self):
        survey_id_list = SurveySubmission.objects.filter(
            submitter__user_id=self.get_object().pk).values_list('survey_id', flat=True).distinct()
        ct = ContentType.objects.get_for_model(Survey)
        return Scheme.objects.filter(
            participations__content_type=ct,
            participations__object_id__in=survey_id_list).values_list('pk', flat=True)

    def get_non_favorite_schemes(self, mode):
        if mode:
            id_list = list(self.get_commented_schemes_id_list())
            id_list.extend(self.get_voted_schemes_id_list())
            id_list.extend(self.get_answered_surveys_schemes_id_list())
            schemes = Scheme.objects.filter(pk__in=id_list).distinct()

            if not CanSeeAllSchemes(request=self.request, obj=self.get_object()).\
                    is_authorized():
                if IsAuthenticated(request=self.request).is_authorized():
                    schemes = schemes.filter(
                        Q(visibility=Scheme.VISIBILITY_PUBLIC) |
                        Q(owners__user__in=(self.request.user, ))
                    )
                else:
                    schemes = schemes.filter(visibility=Scheme.VISIBILITY_PUBLIC)
        else:
            schemes = self.get_schemes()
        return schemes.order_by('-pk')


class UserSettingsView(generic.DetailView):
    model = User
    pk_url_kwarg = 'user_id'
    template_name = 'account/user_settings.html'

    def get_context_data(self, **kwargs):
        kwargs['forms'] = OrderedDict()
        kwargs['forms']['user'] = forms.UsernameForm(
            instance=self.get_object(),
            disable_helptext=True
        )
        kwargs['forms']['usersettings'] = forms.UserSettingsEditForm(
            instance=self.get_object().settings
        )

        kwargs['forms']['notification_options'] = NotificationOptionsForm(
            instance=self.get_object())
        return kwargs


class UserSettingsEditView(MultiModelFormView):
    template_name = 'account/user_settings_edit.html'
    form_classes = (
        ('user', forms.UsernameForm),
        ('usersettings', forms.UserSettingsEditForm)
    )

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['user_id'])

    def get_user_form_kwargs(self, kwargs):
        kwargs['instance'] = self.get_object()
        return kwargs

    def get_usersettings_form_kwargs(self, kwargs):
        kwargs['instance'] = self.get_object().settings
        return kwargs

    def get_success_url(self):
        return reverse('account:settings_detail', kwargs={
            'user_id': self.get_object().pk})

    def form_valid(self):
        self.save_forms()
        return AjaxyInlineRedirectResponse(self.get_success_url())


class UserSettingsDetailView(MultiModelFormView):
    template_name = 'account/user_settings_detail.html'
    form_classes = (
        ('user', forms.UsernameForm),
        ('usersettings', forms.UserSettingsEditForm)
    )

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['user_id'])

    def get_user_form_kwargs(self, kwargs):
        kwargs['instance'] = self.get_object()
        kwargs['disable_helptext'] = True
        return kwargs

    def get_usersettings_form_kwargs(self, kwargs):
        kwargs['instance'] = self.get_object().settings
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserSettingsDetailView, self).get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context


class UserChangePasswordView(generic.UpdateView):
    template_name = 'account/user_change_password.html'
    form_class = PasswordChangeForm

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])

    def get_form(self, form_class):
        return form_class(self.get_object(), data=self.request.POST or None)

    def get_success_url(self):
        messages.success(self.request, _("Salasanasi on vaihdettu. Käytä seuraavan "
                                         "kirjautumisen yhteydessä uutta salasanaasi."))
        return reverse('account:settings', kwargs={'user_id': self.get_object().pk})

    def form_invalid(self, form):
        messages.error(self.request, _("Virhe. Tarkista lomakkeen tiedot."))
        return super(UserChangePasswordView, self).form_invalid(form)


class CloseAccountView(generic.View, generic.detail.SingleObjectMixin):
    model = User
    pk_url_kwarg = 'user_id'
    http_method_names = ['post']
    redirect_url = reverse_lazy('schemes')
    logout = False

    def send_email_notification(self, user):
        send_email(
            _("Käyttäjätilisi on suljettu."),
            'account/email/account_closed.txt',
            {'user': user},
            [user.settings.email],
            user.settings.language
        )

    def post(self, *args, **kwargs):
        user = self.get_object()
        user.status = User.STATUS_ARCHIVED
        user.save()
        self.send_email_notification(user)
        if self.logout and self.request.user == user:
            logout(self.request)
        messages.success(self.request, _("Käyttäjätili %s suljettu.") % user)
        return HttpResponseRedirect(self.redirect_url)


class MessagesListView(generic.ListView):
    model = Message
    paginate_by = 5
    template_name = "account/messages/listing.html"

    user = None
    moderators = None

    FILTER_RECEIVED = "saapuneet"
    FILTER_SENT = "lahetetyt"
    FILTER_QUERY_STRING = "nayta"
    SORT_NEWEST = "uusin"
    SORT_OLDEST = "vanhin"
    SORT_QUERY_STRING = "jarjestys"

    filtering = FILTER_RECEIVED
    order_by = SORT_NEWEST

    def set_filtering(self):
        if self.request.GET.get(self.FILTER_QUERY_STRING):
            self.filtering = self.request.GET.get(self.FILTER_QUERY_STRING)

        # Non-moderators only see their own messages.
        if not self.user.is_moderator:
            if self.filtering == self.FILTER_RECEIVED:
                self.queryset = self.user.received_messages.all()
            elif self.filtering == self.FILTER_SENT:
                self.queryset = self.user.sent_messages.all()

        # Moderators see other moderators messages.
        else:
            if self.filtering == self.FILTER_RECEIVED:
                self.queryset = Message.objects.filter(receivers=self.user)

            elif self.filtering == self.FILTER_SENT:
                self.queryset = Message.objects.filter(sender=self.user)

            # Show one message only once.
            self.queryset = self.queryset.distinct()

    def set_ordering(self):
        if self.request.GET.get(self.SORT_QUERY_STRING):
            self.order_by = self.request.GET.get(self.SORT_QUERY_STRING)

        if self.order_by == self.SORT_NEWEST:
            self.queryset = self.queryset.order_by("-sent")
        elif self.order_by == self.SORT_OLDEST:
            self.queryset = self.queryset.order_by("sent")

    def exclude_deleted(self):
        filtered = []
        for msg in self.queryset:
            if self.user not in msg.deleted_by_users():
                filtered.append(msg)
        self.queryset = filtered

    def get_queryset(self):
        self.user = User.objects.get(pk=self.kwargs["user_id"])
        self.queryset = super(MessagesListView, self).get_queryset()
        self.set_filtering()
        self.set_ordering()
        self.exclude_deleted()
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(MessagesListView, self).get_context_data(**kwargs)
        context["object"] = self.user
        context["highlight_unread"] = self.filtering == self.FILTER_RECEIVED
        return context


class MessageDetailView(generic.DetailView):
    model = Message
    pk_url_kwarg = "message_id"
    template_name = "account/messages/detail.html"

    def get_context_data(self, **kwargs):
        context = super(MessageDetailView, self).get_context_data(**kwargs)
        msg = self.get_object()
        context["object"] = user = User.objects.get(pk=self.kwargs["user_id"])
        if msg.deliveries.user_in_receivers(user):
            msg.deliveries.for_user(user).mark_as_read()
        else:
            context['cannot_delete'] = True
        context["message"] = msg
        return context


class CreateMessageView(generic.CreateView):
    model = Message
    template_name = "account/messages/create.html"
    form_class = forms.MessageForm

    def get_form_kwargs(self):
        kwargs = super(CreateMessageView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super(CreateMessageView, self).get_initial()

        if "message_id" in self.kwargs:
            message_to_respond = Message.objects.get(pk=self.kwargs["message_id"])
            init_msg = "\n\n\n--- {0}: {1}, {2} ---\n{3}"
            init_msg = init_msg.format(
                _("Vastaus viestiin"),
                message_to_respond.subject,
                message_to_respond.sent,
                message_to_respond.message
            )
            initial.update({
                "receivers": [message_to_respond.sender],
                "subject": "Re: {}".format(message_to_respond.subject),
                "message": init_msg
            })

        if "scheme_id" in self.kwargs:
            scheme_id = self.kwargs['scheme_id']
            scheme = get_object_or_404(Scheme, pk=scheme_id)
            if CanEditScheme(request=self.request, obj=scheme).is_authorized():
                receivers = list(scheme.get_participators())
                receivers.remove(self.request.user)
                if not receivers:
                    msg = _("Hankkeella ei vielä ole muiden käyttäjien osallistumisia.")
                else:
                    msg = _("Hankkeeseesi osallistuneet rekisteröityneet käyttäjät on "
                            "valittu viestin vastaanottajiksi")
                messages.info(self.request, msg)
                initial.update({"receivers": receivers})
        else:
            receivers = self.request.GET.get("receivers")
            if receivers:
                initial.update({"receivers": [receivers]})

        return initial

    def get_success_url(self):
        messages.success(self.request, _("Viesti lähetetty."))
        return reverse("account:messages", args=[self.kwargs["user_id"]])

    def get_context_data(self, **kwargs):
        context = super(CreateMessageView, self).get_context_data(**kwargs)
        context["object"] = User.objects.get(pk=self.kwargs["user_id"])
        if "message_id" in self.kwargs:
            context["form_action"] = reverse(
                "account:respond_message",
                args=[self.kwargs["user_id"], self.kwargs["message_id"]]
            )
        else:
            context["form_action"] = reverse(
                "account:create_message",
                args=[self.kwargs["user_id"]]
            )
        return context

    def form_valid(self, form):
        message = form.save(commit=False)
        message.sender = User.objects.get(pk=self.kwargs["user_id"])
        if "message_id" in self.kwargs:
            message.reply_to = Message.objects.get(pk=self.kwargs["message_id"])
        message.save()
        Delivery.objects.save_receivers(message, form.cleaned_data['receivers'])
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Täytä kaikki pakolliset kentät."))
        return super(CreateMessageView, self).form_invalid(form)


class DeleteMessageView(generic.DeleteView):
    model = Message
    pk_url_kwarg = "message_id"

    def delete(self, request, *args, **kwargs):
        msg = self.get_object()
        user = User.objects.get(pk=self.kwargs["user_id"])
        if not msg.deliveries.user_in_receivers(user):
            raise Exception("Can not delete message if user is not a receiver")

        # removing feedback deletes it from every moderator - not in use for now
        """
        if msg.is_feedback():
            for d in msg.deliveries.all():
                d.mark_as_deleted()
        else:
        """
        msg.deliveries.for_user(user).mark_as_deleted()

        messages.success(self.request, _("Viesti poistettu postilaatikostasi."))
        return HttpResponseRedirect(reverse("account:messages", args=[user.pk]))


class NotificationOptionsEditView(UpdateView):
    model = User
    pk_url_kwarg = 'user_id'
    form_class = NotificationOptionsForm
    template_name = 'account/notification_options/options_edit.html'

    def get_success_url(self):
        return reverse('account:notification_options_detail', kwargs={
            'user_id': self.kwargs['user_id']})


class NotificationOptionsDetailView(DetailView):
    model = User
    pk_url_kwarg = 'user_id'
    form_class = NotificationOptionsForm
    template_name = 'account/notification_options/options_detail.html'

    def get_context_data(self, **kwargs):
        kwargs['forms'] = OrderedDict()
        kwargs['forms']['notification_options'] = NotificationOptionsForm(
            instance=self.get_object())
        return kwargs

