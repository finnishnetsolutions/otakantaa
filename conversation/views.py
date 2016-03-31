# coding: utf-8
from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.utils.translation import ugettext_lazy as _, ugettext
from conversation.forms import EditCommentForm, DeleteCommentForm
from conversation.models import Vote, Voter
from conversation.utils import vote, set_vote_cookie
from libs.ajaxy.responses import AjaxyInlineRedirectResponse

from .forms import CommentForm, CommentFormAnon, CommentResponseForm, \
    CommentResponseFormAnon
from .models import Comment, Conversation
from content import conversation_perms as perms
from okmoderation.utils import get_moderated_form_class


class PostCommentView(CreateView):
    model = Comment
    template_name = 'comments/comment_form.html'
    comment = None

    def get_form_class(self):
        if self.request.user.is_authenticated():
            return CommentForm
        else:
            return CommentFormAnon

    def get_conversation_object(self, **kwargs):
        return get_object_or_404(Conversation, pk=self.kwargs['conversation_id'])

    def get_context_data(self, **kwargs):
        context = super(PostCommentView, self).get_context_data(**kwargs)
        context['conversation'] = self.get_conversation_object()
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=400)

    def create_new_comment_object(self, form):
        comment = form.save(commit=False)
        comment.conversation = self.get_conversation_object()
        scheme = comment.conversation.get_parent_scheme()
        if self.request.user.is_authenticated():
            comment.user = self.request.user

            # check if user is scheme owner or moderator
            owners = scheme.owners.unique_users()
            if self.request.user in owners or self.request.user.is_moderator:
                comment.admin_comment = True

        premoderation = getattr(scheme, 'premoderation', False)
        if premoderation:
            comment.is_public = False
        return comment

    def get_success_url(self):
        if self.request.is_ajax():
            return AjaxyInlineRedirectResponse(
                reverse('conversation:comments_preview', kwargs={
                    'conversation_id': self.comment.conversation.pk}))
        # fallback if javascript disabled
        messages.success(self.request, ugettext("Kommenttisi on tallennettu"))
        pd = self.comment.conversation.get_parent_participation()
        return HttpResponseRedirect(reverse('content:participation:conversation_detail',
                       kwargs={'participation_detail_id': pd.pk,
                               'scheme_id': pd.scheme_id}))

    def form_valid(self, form):
        comment = self.create_new_comment_object(form)
        comment.save()
        if not comment.is_public:
            if comment.target_comment:
                msg = "Vastauksesi on tallennettu."
            else:
                msg = "Kommenttisi on tallennettu."
            messages.success(self.request, ugettext(msg))

        self.comment = comment
        return self.get_success_url()


class PostResponseView(PostCommentView):
    model = Comment
    template_name = 'comments/comment_response_form.html'

    def get_form_class(self):
        if self.request.user.is_authenticated():
            return CommentResponseForm
        else:
            return CommentResponseFormAnon

    def get_context_data(self, **kwargs):
        context = super(PostCommentView, self).get_context_data(**kwargs)
        context['comment'] = self.get_target_comment()
        return context

    def get_target_comment(self):
        return get_object_or_404(Comment, pk=self.kwargs['comment_id'])

    def get_success_url(self):
        if self.request.is_ajax():
            return AjaxyInlineRedirectResponse(
                reverse('conversation:comment_detail_block', kwargs={
                    'comment_id': self.kwargs['comment_id'],
                    'conversation_id': self.kwargs['conversation_id']}))
        # fallback if javascript disabled
        messages.success(self.request, ugettext("Vastauksesi on tallennettu"))
        return HttpResponseRedirect(reverse('conversation:comment_detail', kwargs={
            'conversation_id': self.kwargs['conversation_id'],
            'comment_id': self.kwargs['comment_id']}))

    def create_new_comment_object(self, form):
        comment = super(PostResponseView, self).create_new_comment_object(form)
        comment.target_comment = self.get_target_comment()
        return comment


class PreviewCommentsView(TemplateView):
    template_name = 'comments/comments_preview.html'

    def get_context_data(self, **kwargs):
        kwargs['conversation'] = get_object_or_404(Conversation,
                                                   pk=self.kwargs['conversation_id'])
        return kwargs


class CommentDetailView(DetailView):
    pk_url_kwarg = 'comment_id'
    model = Comment


class VoteCommentView(TemplateView):
    http_method_names = ['post']
    template_name = 'comments/comment_voting.html'
    choice = Vote.VOTE_DOWN

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        comment = Comment.objects.get(pk=self.kwargs['comment_id'])
        vote_obj = vote(request, Comment, comment.pk, self.choice)

        context['comment'] = comment

        # Set the cookie for voting.
        response = super(VoteCommentView, self).render_to_response(context)
        try:
            voter_id = vote_obj.voter.voter_id
        except AttributeError:
            voter_id = None
        # needs to set cookie for request too. permission checks will then have fresh data
        self.request.COOKIES[Voter.VOTER_COOKIE] = voter_id
        return set_vote_cookie(request, response, voter_id)


class RemoveCommentVoteView(View):
    pk_url_kwarg = 'comment_id'
    template_name = 'comments/comment_voting.html'

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs.get(self.pk_url_kwarg, None))

    def get_vote_object(self, comment):
        return comment.votes.get(voter__user_id=self.request.user.pk)

    def post(self, request, **kwargs):
        comment = self.get_object()
        vote_obj = self.get_vote_object(comment)
        vote_obj.delete()
        return render_to_response(self.template_name,
                                  {'comment': comment, 'request': request})

    def get(self, request, *args, **kwargs):
        raise Exception("Forbidden action")


class ModeratorFormMixIn(object):
    def get_form_class(self):
        if not perms.OwnsComment(request=self.request, obj=self.get_object()).\
                is_authorized():
            return get_moderated_form_class(self.form_class, self.request.user)
        return self.form_class


class RemoveCommentView(ModeratorFormMixIn, UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'comments/comment_confirm_delete.html'
    form_class = DeleteCommentForm

    def form_valid(self, form):
        super(RemoveCommentView, self).form_valid(form)
        comment = self.get_object()
        comment.is_removed = True
        comment.removed_by = self.request.user
        comment.save()
        return render_to_response('comments/comment_item_removed.html',
                                  {'comment': comment})


class EditCommentView(ModeratorFormMixIn, UpdateView):
    model = Comment
    form_class = EditCommentForm
    template_name = 'otakantaa/inline_edit_base_form.html'
    pk_url_kwarg = 'comment_id'

    def form_valid(self, form):
        super(EditCommentView, self).form_valid(form)
        comment = form.instance
        return render_to_response('comments/comment_text.html', {'comment': comment})

