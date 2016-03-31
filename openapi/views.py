# coding=utf-8

from __future__ import unicode_literals

from functools import wraps
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from content.models import Scheme, ParticipationDetails
from conversation.models import Conversation
from openapi.serializers import PaginatedQuestionSerializer
from .serializers import PaginatedSchemeSerializer, \
    PaginatedConversationSerializer, PaginatedSurveySerializer, PaginatedCommentSerializer
from organization.models import Organization
from survey.models import Survey, SurveyElement
from tagging.models import Tag

from . import serializers


def with_serializer(serializer_class):
    def _deco(method):
        @wraps(method)
        def _inner(self, *args, **kwargs):
            old_serializer_class = self.serializer_class
            try:
                self.serializer_class = serializer_class
                return method(self, *args, **kwargs)
            finally:
                self.serializer_class = old_serializer_class
        return _inner
    return _deco


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.normal()
    serializer_class = serializers.OrganizationSerializer
    paginate_by = 50

    @with_serializer(serializers.OrganizationDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the organization.
        ---
        response_serializer: ..serializers.OrganizationDetailSerializer
        """
        return super(OrganizationViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all active organizations.
        ---
        response_serializer: ..serializers.PaginatedOrganizationSerializer
        """
        return super(OrganizationViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='schemes')
    def list_schemes(self, request, pk=None):
        """
        Returns a paginated list of schemes targeting the organization.
        ---
        response_serializer: ..serializers.PaginatedSchemeSerializer
        """
        org = get_object_or_404(Organization, pk=pk)
        schemes = Scheme.objects.filter(
            visibility=Scheme.VISIBILITY_PUBLIC,
            owners__organization_id=org.pk).order_by('-published')
        page = self.paginate_queryset(schemes)
        context = self.get_serializer_context()
        serializer = PaginatedSchemeSerializer(instance=page, context=context)
        return Response(serializer.data)


class SchemeViewSet(viewsets.ReadOnlyModelViewSet):
    paginate_by = 50
    max_paginate_by = 50

    queryset = Scheme.objects\
        .filter(visibility=Scheme.VISIBILITY_PUBLIC)\
        .order_by('-published')
    serializer_class = serializers.SchemeSerializer

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all public schemes.

        Schemes are sorted from newest to oldest.
        ---
        serializer: ..serializers.PaginatedSchemeSerializer
        """

        return super(SchemeViewSet, self).list(request, *args, **kwargs)

    @with_serializer(serializers.SchemeDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the scheme.
        ---
        response_serializer: ..serializers.SchemeDetailSerializer
        """
        return super(SchemeViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='conversations')
    def list_conversations(self, request, pk=None):
        """
        Returns a paginated list of conversations associated with the scheme.
        ---
        response_serializer: ..serializers.PaginatedConversationSerializer
        """
        # TODO check scheme publicity
        scheme = get_object_or_404(Scheme.objects.filter(
            visibility=Scheme.VISIBILITY_PUBLIC), pk=pk)
        ct = ContentType.objects.get_for_model(Conversation)
        pd_conversations = ParticipationDetails.objects.filter(
            status=ParticipationDetails.STATUS_PUBLISHED, scheme__pk=scheme.pk,
            content_type_id=ct)
        page = self.paginate_queryset(pd_conversations)
        context = self.get_serializer_context()
        serializer = PaginatedConversationSerializer(instance=page, context=context)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='surveys')
    def list_surveys(self, request, pk=None):
        """
        Returns a paginated list of surveys associated with the scheme.
        ---
        response_serializer: ..serializers.PaginatedSurveySerializer
        """
        # TODO check scheme publicity
        scheme = get_object_or_404(Scheme.objects.filter(
            visibility=Scheme.VISIBILITY_PUBLIC), pk=pk)
        ct = ContentType.objects.get_for_model(Survey)
        pd_surveys = ParticipationDetails.objects.filter(
            status=ParticipationDetails.STATUS_PUBLISHED, scheme__pk=scheme.pk,
            content_type_id=ct)
        page = self.paginate_queryset(pd_surveys)
        context = self.get_serializer_context()
        serializer = PaginatedSurveySerializer(instance=page, context=context)
        return Response(serializer.data)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    paginate_by = 50
    max_paginate_by = 50
    queryset = ParticipationDetails.objects.filter(
        scheme__visibility=Scheme.VISIBILITY_PUBLIC,
        status=ParticipationDetails.STATUS_PUBLISHED,
        content_type_id=ContentType.objects.get_for_model(Conversation)
    )
    serializer_class = serializers.ConversationSerializer

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all public conversations.

        Conversations are sorted from newest to oldest.
        ---
        serializer: ..serializers.ConversationDetailSerializer
        """

        return super(ConversationViewSet, self).list(request, *args, **kwargs)

    @with_serializer(serializers.ConversationDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the Conversation.
        ---
        response_serializer: ..serializers.ConversationDetailSerializer
        """
        return super(ConversationViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='comments')
    def list_comments(self, request, pk=None):
        """
        Returns a paginated list of conversations public comments.
        ---
        response_serializer: ..serializers.PaginatedCommentSerializer
        """
        conversation = get_object_or_404(Conversation, pk=pk)
        comments = conversation.public_comments_filter_removed().order_by(
            'target_comment_id', 'pk')
        page = self.paginate_queryset(comments)
        context = self.get_serializer_context()
        serializer = PaginatedCommentSerializer(instance=page, context=context)
        return Response(serializer.data)


class SurveyViewSet(viewsets.ReadOnlyModelViewSet):
    paginate_by = 50
    max_paginate_by = 50
    queryset = ParticipationDetails.objects.filter(
        scheme__visibility=Scheme.VISIBILITY_PUBLIC,
        status=ParticipationDetails.STATUS_PUBLISHED,
        content_type_id=ContentType.objects.get_for_model(Survey)
    )
    serializer_class = serializers.SurveySerializer

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all public surveys.

        Surveys are sorted from newest to oldest.
        ---
        serializer: ..serializers.SurveyDetailSerializer
        """

        return super(SurveyViewSet, self).list(request, *args, **kwargs)

    @with_serializer(serializers.SurveyDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the Survey.
        ---
        response_serializer: ..serializers.SurveyDetailSerializer
        """
        return super(SurveyViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='questions')
    def list_questions(self, request, pk=None):
        """
        Returns a paginated list of questions in survey.
        ---
        response_serializer: ..serializers.PaginatedQuestionSerializer
        """
        survey = get_object_or_404(Survey, pk=pk)
        questions = survey.elements.questions()
        page = self.paginate_queryset(questions)
        context = self.get_serializer_context()
        serializer = PaginatedQuestionSerializer(instance=page, context=context)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

    paginate_by = 50
    max_paginate_by = 50

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all tags.
        ---
        response_serializer: ..serializers.PaginatedTagSerializer
        """
        return super(TagViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns basic details about the tag.
        """
        return super(TagViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='schemes')
    def list_schemes(self, request, pk=None):
        """
        Returns a paginated list of schemes associated with the tag.
        ---
        response_serializer: ..serializers.PaginatedSchemeSerializer
        """
        tag = get_object_or_404(Tag, pk=pk)
        schemes = Scheme.objects.filter(visibility=Scheme.VISIBILITY_PUBLIC,
                                        tags__pk=tag.pk).order_by('-published')
        page = self.paginate_queryset(schemes)
        context = self.get_serializer_context()
        serializer = PaginatedSchemeSerializer(instance=page, context=context)
        return Response(serializer.data)
