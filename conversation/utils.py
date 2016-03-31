# coding=utf-8

from __future__ import unicode_literals

from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.utils import IntegrityError

from account.utils import get_client_identifier
from content.models import ParticipationDetails
from .models import Vote, Voter
from .forms import CommentForm, CommentFormAnon, CommentResponseForm, \
    CommentResponseFormAnon


# Comments
def get_form(request, *args, **kwargs):
    response = kwargs.get('get_response_form', None)

    if request.user.is_authenticated():
        klass = CommentForm if not response else CommentResponseForm
    else:
        klass = CommentFormAnon if not response else CommentResponseFormAnon
    return klass()


# Votes
def get_voter(request, create=True):
    """ Returns voter object for currently logged in user or non-logged in user.
        Use create=False if you only want to get the voter, but not to create one.
        Usually perms should use create=False. """
    voter = None

    try:
        user_id = request.user.pk
    except AttributeError:
        user_id = None

    cookie_voter_id = request.COOKIES.get(Voter.VOTER_COOKIE, None)

    if user_id:
        try:
            voter = Voter.objects.get(user_id=user_id)
        except Voter.DoesNotExist:
            if cookie_voter_id:
                voter = Voter.objects.filter(
                    voter_id=cookie_voter_id
                ).order_by("-user_id").first()
                if voter and not voter.user_id:
                    voter.user_id = user_id
                    voter.save()

    elif cookie_voter_id:

        voter = Voter.objects.filter(
            voter_id=cookie_voter_id
        ).order_by("-user_id").first()

    if not voter and create:
        voter = Voter(user_id=user_id, voter_id=uuid4().hex)
        voter.save()
    return voter


def vote(request, target_class, object_pk, choice):
    voter = get_voter(request)
    client_identifier = get_client_identifier(request)
    content_object = target_class._default_manager.get(pk=object_pk)
    try:
        with transaction.atomic():
            vote_object = Vote(
                voter=voter,
                client_identifier=client_identifier,
                content_object=content_object,
                choice=choice,
            )
            vote_object.save()
        return vote_object
    except IntegrityError:
        return False


def get_vote(request, target_class, object_pk):
    try:
        vote_object = Vote.objects.get(
            voter=get_voter(request, create=False),
            object_id=object_pk,
            content_type=ContentType.objects.get_for_model(target_class)
        )
    except Vote.DoesNotExist:
        return None
    else:
        return vote_object


def set_vote_cookie(request, response, voter_id):
    response.set_cookie(
        Voter.VOTER_COOKIE,
        voter_id,
        httponly=True,
        secure=request.is_secure()
    )
    return response
