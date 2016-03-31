# coding=utf-8

from __future__ import unicode_literals

from django import template

from .. import perms, utils
from conversation.models import Comment, Vote

register = template.Library()


@register.simple_tag(takes_context=True)
def get_comment_form(context, varname='form', *args, **kwargs):
    context[varname] = utils.get_form(context['request'], *args, **kwargs)
    return ''


@register.simple_tag(takes_context=True)
def get_voting_disabled_class(context, obj, varname='disabled_class'):
    context[varname] = ''
    if not perms.CanVoteComment(request=context['request'], obj=obj).is_authorized():
        context[varname] = ' disabled'
    return ''


@register.simple_tag(takes_context=True)
def get_vote_icon(context, obj, for_choice='up'):
    vote = utils.get_vote(context['request'], Comment, obj.pk)

    choice = Vote.VOTE_UP if for_choice == 'up' else Vote.VOTE_DOWN
    icons = {
        'voted': {'up': 'thumbs-up', 'down': 'thumbs-down'},
        'not_voted': {'up': 'thumbs-o-up', 'down': 'thumbs-o-down'}
    }
    varname = 'icon_thumb_{}'.format(for_choice)

    if vote is not None and vote.choice == choice:
        context[varname] = icons['voted'][for_choice]
    else:
        context[varname] = icons['not_voted'][for_choice]
    return ''


@register.filter(name="vote_balance")
def comment_vote_balance(comment):
    balance = sum([vote.choice for vote in comment.votes.all()])
    return "+{}".format(balance) if balance > 0 else balance


@register.filter(name="public")
def public_comments(comments):
    return [comment for comment in comments if comment.is_public]


@register.filter(name="initial")
def initial_comments(comments):
    return [comment for comment in comments if comment.target_comment_id is None]


@register.filter(name="visible")
def visible_comments(comments):
    return [comment for comment in comments if comment.is_removed is False]
