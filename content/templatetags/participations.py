# coding=utf-8

from __future__ import unicode_literals

from django import template

register = template.Library()


def participations_user_can_see(scheme, user, querystring=None):
    if querystring is None:
        querystring = scheme.participations.all()
    if user in scheme.owners.unique_users() or \
                    user.is_authenticated() and user.is_moderator:
        participations = list(querystring.open_or_draft())
    else:
        participations = list(querystring.open())
    participations.extend(querystring.closed())
    # set() removese duplicates
    return list(set(participations))


@register.assignment_tag(takes_context=True)
def get_participations(context, scheme):
    user = context['request'].user
    return participations_user_can_see(scheme, user)


@register.assignment_tag(takes_context=True)
def get_surveys(context, scheme):
    user = context["request"].user
    querystring = scheme.participations.surveys()
    return participations_user_can_see(scheme, user, querystring)


@register.assignment_tag(takes_context=True)
def get_conversations(context, scheme):
    user = context["request"].user
    querystring = scheme.participations.conversations()
    test = participations_user_can_see(scheme, user, querystring)
    return test
