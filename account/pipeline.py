# coding=utf-8

from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.template.defaultfilters import date

from social.pipeline.partial import partial


""" AUTH FUNCTIONS """


def performed_action(strategy, *args, **kwargs):
    return {"action": strategy.session_get("action")}


def social_user(strategy, backend, uid, user=None, *args, **kwargs):
    """
    Mostly copied from social's original function.
    Only error message and redirect changed.
    """
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            messages.error(strategy.request, _("Facebook-tili on jo käytössä."))
            return redirect("account:settings", user_id=user.pk)
        elif not user:
            user = social.user
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}


def social_login_possible(strategy, user, social, action, *args, **kwargs):
    if action == "login" and social is None:
        messages.info(
            strategy.request,
            _("Facebook-tiliä ei ole yhdistetty. Rekisteröidy "
                "Facebook-tunnuksillasi tai yhdistä se jo olemassaolevaan "
                "Otakantaa.fi-tunnukseen oma sivun asetuksista.")
        )
        return redirect("account:login")


def prevent_duplicate_signup(strategy, user, social, action, *args, **kwargs):
    if action == "signup" and social:
        messages.info(strategy.request, _("Facebook-tili on jo käytössä."))
        return redirect("account:signup_choices")


@partial
def social_signup(strategy, action, is_new, response, *args, **kwargs):
    if action == "signup" and is_new:
        new_user = strategy.request.session.get("new_user")
        if new_user:
            del strategy.request.session["new_user"]
            return {"user": new_user}
        else:
            details = kwargs["details"]
            strategy.request.session["fb_id"] = response.get("id")
            strategy.request.session["fb_email"] = details.get("email")
            strategy.request.session["fb_first_name"] = details.get("first_name")
            strategy.request.session["fb_last_name"] = details.get("last_name")
            return redirect("account:signup_facebook")


def logged_user(strategy, user, *args, **kwargs):
    if user is None:
        user = strategy.request.user
        if user.is_authenticated():
            return {"user": user}


def set_messages(strategy, is_new, new_association, user, *args, **kwargs):
    if is_new and new_association:
        return redirect("account:activate")

    elif not is_new and new_association:
        messages.success(strategy.request, _("Facebook-yhteys luotu. Voit jatkossa "
                                             "kirjautua palveluun "
                                             "facebook-tunnuksillasi."))
    elif not is_new and not new_association and user.is_authenticated():
        messages.success(strategy.request, _("Tervetuloa! Käytit palvelua viimeksi %s.") %
                         date(user.last_login, 'DATETIME_FORMAT'))


""" DISCONNECT FUNCTIONS """


def set_disconnect_messages(strategy, user, *args, **kwargs):
    messages.success(strategy.request, _("Facebook-yhteys poistettu."))
