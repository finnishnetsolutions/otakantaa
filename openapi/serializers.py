# coding=utf-8

from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.reverse import reverse

from account.models import User
from content.models import Scheme, SchemeOwner, ParticipationDetails
from conversation.models import Comment, Conversation
from libs.fimunicipality.models import Municipality
from openapi.base_serializers import MultilingualTextField, MultilingualUrlField
from organization.models import Organization
from survey.models import Survey, SurveyOption, SurveyQuestion
from tagging.models import Tag

from . import base_serializers as base


class SchemeStatusField(serializers.ChoiceField):
    FRIENDLY_STATUSES = (
        (Scheme.STATUS_DRAFT, "draft"),
        (Scheme.STATUS_PUBLISHED, "published"),
        (Scheme.STATUS_CLOSED, "completed"),
    )

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = self.FRIENDLY_STATUSES
        kwargs['help_text'] = ' or '.join(
            map(lambda v: '"{}"'.format(v),
                [status[1] for status in self.FRIENDLY_STATUSES])
        )
        super(SchemeStatusField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return dict(self.FRIENDLY_STATUSES)[value]
        except KeyError:
            return "unknown"


class SchemeSerializer(base.HyperlinkedModelSerializer):
    title = MultilingualTextField(help_text="title of the Scheme")
    status = SchemeStatusField()

    class Meta:
        model = Scheme
        fields = ('url', 'title', 'status', )


class ParticipationBaseSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    webUrl = MultilingualUrlField()

    def get_url(self, obj):
        return reverse('openapi:{}-detail'.format(obj.content_type.model),
                       kwargs={'pk': obj.pk}, request=self.context['request'])

    def get_is_closed(self, obj):
        return not obj.is_open()


class ConversationSerializer(ParticipationBaseSerializer):
    title = MultilingualTextField(help_text="title of the conversation")
    is_closed = serializers.SerializerMethodField(help_text="conversation has expired")

    class Meta:
        model = ParticipationDetails
        fields = ('url', 'title', 'is_closed', )


class SurveySerializer(ParticipationBaseSerializer):
    title = MultilingualTextField(help_text="title of the survey")
    is_closed = serializers.SerializerMethodField(help_text="survey has expired")

    class Meta:
        model = ParticipationDetails
        fields = ('url', 'title', 'is_closed', )


class SurveyQuestionSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        source='content_object.elements.questions.count',
        help_text="number of questions in survey")
    url = serializers.SerializerMethodField('_questions_url',
                                            help_text="API URL for the questions "
                                                      "in survey")

    def _questions_url(self, obj):
        return reverse('openapi:survey-questions',
                       kwargs={'pk': obj.content_object.pk},
                       request=self.context['request'])


class SurveyDetailSerializer(SurveySerializer):
    expires = serializers.DateTimeField(source='expiration_date',
                                        help_text="when survey expires timestamp")
    description = MultilingualTextField(
        source='description_plaintext',
        help_text="description for survey without formatting")
    questions = SurveyQuestionSerializer(source='*',
                                         help_text="Survey questions summary")

    class Meta:
        model = ParticipationDetails
        fields = ('url', 'title', 'description', 'is_closed', 'expires', 'questions',
                  'webUrl')


class ConversationCommentsSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        source='content_object.public_comments_filter_removed.count',
        help_text="number of public comments the conversation has received")
    url = serializers.SerializerMethodField('_comments_url',
                                            help_text="API URL for the comments "
                                                      "in conversation")

    def _comments_url(self, obj):
        return reverse('openapi:conversation-comments',
                       kwargs={'pk': obj.content_object.pk},
                       request=self.context['request'])


class ConversationDetailSerializer(ConversationSerializer):
    expires = serializers.DateTimeField(source='expiration_date',
                                        help_text="when conversation expires timestamp")
    description = MultilingualTextField(
        source='description_plaintext',
        help_text="description for conversation without formatting")
    comments = ConversationCommentsSerializer(source='*',
                                              help_text="Conversation comments summary")

    class Meta:
        model = ParticipationDetails
        fields = ('url', 'title', 'description', 'is_closed', 'expires', 'comments',
                  'webUrl')


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', )


class OrganizationSerializer(base.HyperlinkedModelSerializer):
    name = MultilingualTextField(help_text="name of the Organization")

    class Meta:
        model = Organization
        fields = ('url', 'name', )


class OrganizationSchemesSummarySerializer(serializers.Serializer):
    url = serializers.SerializerMethodField('_schemes_url',
                                            help_text="API URL for Schemes owned by "
                                                      "Organization")
    count = base.SerializerMethodIntegerField('_schemes_count',
                                              help_text="number of public Schemes "
                                                        "owned by Organization")

    def _schemes_count(self, obj):
        return Scheme.objects.filter(visibility=Scheme.VISIBILITY_PUBLIC,
                                     owners__organization_id=obj.pk).count()

    def _schemes_url(self, obj):
        return reverse('openapi:organization-schemes', kwargs={'pk': obj.pk},
                       request=self.context['request'])


class OrganizationDetailSerializer(base.HyperlinkedModelSerializer):
    name = MultilingualTextField(help_text="name of the Organization")
    description = MultilingualTextField(source='description_plaintext',
                                        help_text="description of the Organization "
                                                  "without formatting")
    schemes = OrganizationSchemesSummarySerializer(
        source='*', help_text="summary of Schemes owned by Organization")
    webUrl = MultilingualUrlField()

    class Meta:
        model = Organization
        fields = ('url', 'name', 'description', 'schemes', 'webUrl', )


class SchemeOwnersSerializer(serializers.ModelSerializer):
    user = UserSerializer(help_text="owner user - if organization exists then user is a"
                                    "organization admin")
    organization = serializers.SerializerMethodField(help_text="owner organization")

    def get_organization(self, obj):
        if obj.organization:
            return OrganizationSerializer(obj.organization, context=self.context).data
        return None

    class Meta:
        model = SchemeOwner
        fields = ('user', 'organization')


class SchemeConversationSummarySerializer(serializers.Serializer):
    url = serializers.SerializerMethodField('_conversations_url',
                                            help_text="API URL for Conversations "
                                                      "associated with the Scheme")
    count = base.SerializerMethodIntegerField('_conversations_count',
                                              help_text="number of public Conversations "
                                                        "associated with the Scheme")

    def _conversations_count(self, obj):
        ct = ContentType.objects.get_for_model(Conversation)
        data = obj.participations.filter(status=ParticipationDetails.STATUS_PUBLISHED,
                                         content_type_id=ct)
        return data.count()

    def _conversations_url(self, obj):
        return reverse('openapi:scheme-conversations', kwargs={'pk': obj.pk},
                       request=self.context['request'])


class SchemeSurveySummarySerializer(serializers.Serializer):
    url = serializers.SerializerMethodField('_survey_url',
                                            help_text="API URL for Surveys "
                                                      "associated with the Scheme")
    count = base.SerializerMethodIntegerField('_survey_count',
                                              help_text="number of public Surveys "
                                                        "associated with the Scheme")

    def _survey_count(self, obj):
        ct = ContentType.objects.get_for_model(Survey)
        data = obj.participations.filter(status=ParticipationDetails.STATUS_PUBLISHED,
                                         content_type_id=ct)
        return data.count()

    def _survey_url(self, obj):
        return reverse('openapi:scheme-surveys', kwargs={'pk': obj.pk},
                       request=self.context['request'])


class SchemeTagsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(help_text="the tag")

    class Meta:
        model = Tag
        fields = ('name', )


class SchemeMunicipalitiesSerializer(serializers.ModelSerializer):

    name_fi = serializers.CharField(help_text="name of municipality in finnish")
    name_sv = serializers.CharField(help_text="name of municipality in swedish")

    class Meta:
        model = Municipality
        fields = ('name_fi', 'name_sv')


class SchemeDetailSerializer(base.HyperlinkedModelSerializer):
    title = MultilingualTextField(help_text="title for the Scheme")
    lead_text = MultilingualTextField(help_text="Lead text for the Scheme")
    description = MultilingualTextField(source='description_plaintext',
                                        help_text="description for the Scheme without "
                                                  "formatting")
    owners = serializers.SerializerMethodField(
        source="*",
        help_text="Scheme authors/owners. Returns an array of owners. If "
                  "organization exists then user is the admin of the owner organization. "
                  "<br>{'user': {'username': 'John Doe'}, <br>'organization': "
                  "OrganizationSerializer {<br>url (field): object detail API URL,<br>"
                  "name (MultilingualTextField): name of the Organization}}")

    status = SchemeStatusField()
    published = serializers.DateTimeField(help_text="timestamp when the scheme was "
                                                    "published")
    webUrl = MultilingualUrlField()

    tags = SchemeTagsSerializer(many=True, help_text="Scheme tags")
    target_municipalities = SchemeMunicipalitiesSerializer(
        many=True, help_text="Municipalities connected to Scheme")

    conversations = SchemeConversationSummarySerializer(
        source='*', help_text="scheme conversations")
    surveys = SchemeSurveySummarySerializer(source='*', help_text="scheme surveys")

    def get_owners(self, data):
        return SchemeOwnersSerializer(
            data.owners.real(), many=True, context=self.context).data

    class Meta:
        model = Scheme
        fields = ('url', 'published', 'title', 'status', 'lead_text', 'description',
                  'owners', 'tags', 'target_municipalities', 'conversations', 'surveys',
                  'webUrl')


class TagSchemesSummarySerializer(serializers.Serializer):
    url = serializers.SerializerMethodField('_schemes_url',
                                            help_text="API URL for Schemes associated "
                                                      "with the Tag")
    count = base.SerializerMethodIntegerField('_schemes_count',
                                              help_text="number of public Schemes "
                                                        "associated with the Tag")

    def _schemes_count(self, obj):
        return Scheme.objects.filter(visibility=Scheme.VISIBILITY_PUBLIC,
                                     tags__pk=obj.pk).count()

    def _schemes_url(self, obj):
        return reverse('openapi:tag-schemes', kwargs={'pk': obj.pk},
                       request=self.context['request'])


class TagSerializer(base.HyperlinkedModelSerializer):
    name = MultilingualTextField(help_text='label of the Tag')
    schemes = TagSchemesSummarySerializer(source='*')

    class Meta:
        model = Tag
        fields = ('url', 'name', 'schemes', )


class CommentAuthorSerializer(serializers.Serializer):
    anonymous = serializers.BooleanField(source='is_anonymous',
                                         help_text="true if the user was not logged in "
                                                   "when posting the comment; false "
                                                   "otherwise.")
    name = serializers.CharField(source='user_name',
                                 help_text="name given by non-logged-in user when "
                                           "posting the comment; null if the user was "
                                           "logged in")
    user = UserSerializer(help_text="logged in user details; null if the user was "
                                    "anonymous")

    class Meta:
        fields = ('anonymous', 'name', 'user', )


class CommentSerializer(base.HyperlinkedModelSerializer):
    pk = serializers.IntegerField(help_text="primary key for comment")
    target_comment_id = serializers.IntegerField(
        help_text="answer to a comment, refers to primary key")
    quote_id = serializers.IntegerField(
        help_text="quoted a comment, refers to primary key")
    is_admin_comment = serializers.BooleanField(
        source='admin_comment', help_text="true if comment is written by an admin")
    author = CommentAuthorSerializer(source='*', help_text="comment creator details")
    title = serializers.CharField(help_text="title for comment")
    comment = serializers.CharField(help_text="comment text content")
    created = serializers.DateTimeField(help_text="timestamp when the comment was posted")

    class Meta:
        model = Comment
        fields = ('pk', 'target_comment_id', 'quote_id', 'is_admin_comment', 'created',
                  'title', 'comment', 'author')


class QuestionOptionsSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(help_text="primary key for option")
    text = serializers.CharField(help_text="answer option")

    class Meta:
        model = SurveyOption
        fields = ('pk', 'text', )


class QuestionAnswersSerializer(serializers.ModelSerializer):
    option_id = serializers.IntegerField(help_text="answer refers to option primary key")
    text = serializers.CharField(help_text="textual answer to question")

    class Meta:
        model = SurveyOption
        fields = ('text', 'option_id')


class QuestionSerializer(serializers.ModelSerializer):

    question = MultilingualTextField(source='text', help_text='the question')
    type = serializers.SerializerMethodField(help_text="type of question")
    instruction = MultilingualTextField(
        source='instruction_text', help_text="instructions for answering the question")

    options = QuestionOptionsSerializer(many=True,
                                        help_text="answer options for question")

    answers = QuestionAnswersSerializer(many=True,
                                        help_text="submitted answers to question")

    def get_type(self, obj):
        return obj.get_type_display()

    class Meta:
        model = SurveyQuestion
        fields = ('question', 'type', 'instruction', 'options', 'answers')


class PaginatedSchemeSerializer(base.PaginationSerializer):
    results = SchemeSerializer(many=True)

    class Meta:
        object_serializer_class = SchemeSerializer


class PaginatedCommentSerializer(base.PaginationSerializer):
    results = CommentSerializer(many=True)

    class Meta:
        object_serializer_class = CommentSerializer


class PaginatedQuestionSerializer(base.PaginationSerializer):
    results = QuestionSerializer(many=True)

    class Meta:
        object_serializer_class = QuestionSerializer


class PaginatedConversationSerializer(base.PaginationSerializer):
    results = ConversationSerializer(many=True)

    class Meta:
        object_serializer_class = ConversationDetailSerializer


class PaginatedSurveySerializer(base.PaginationSerializer):
    results = SurveySerializer(many=True)

    class Meta:
        object_serializer_class = SurveyDetailSerializer


class PaginatedTagSerializer(base.PaginationSerializer):
    results = TagSerializer(many=True)

    class Meta:
        object_serializer_class = TagSerializer


class PaginatedOrganizationSerializer(base.PaginationSerializer):
    results = OrganizationSerializer(many=True)

    class Meta:
        object_serializer_class = OrganizationSerializer
