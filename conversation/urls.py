# coding: utf-8
from django.conf.urls import url
from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import obj_by_pk, combo
from libs.permitter.decorators import check_perm

from . import views
from .perms import CanVoteComment, CanRemoveComment, CanCommentConversation, \
    CanCancelVote, CanEditComment
from .models import Conversation, Comment, Vote

conv_by_pk = obj_by_pk(Conversation, 'conversation_id')
comment_by_pk = obj_by_pk(Comment, 'comment_id')


# Comments
urlpatterns = [
    url(r'^(?P<conversation_id>\d+)/kommentit/$', views.PreviewCommentsView.as_view(),
        name='comments_preview'),
    url(r'^(?P<conversation_id>\d+)/kommentti/(?P<comment_id>\d+)/$',
        views.CommentDetailView.as_view(template_name='comments/comment_detail.html'),
        name='comment_detail'),
    url(r'^(?P<conversation_id>\d+)/kommentti/(?P<comment_id>\d+)/lainaus/'
        r'(?P<quote_id>\d+)/$',
        views.CommentDetailView.as_view(template_name='comments/comment_detail.html'),
        name='comment_detail'),
    url(r'^(?P<conversation_id>\d+)/kommenttilohko/(?P<comment_id>\d+)/$',
        views.CommentDetailView.as_view(
            template_name='comments/comment_and_responses_block.html'),
        name='comment_detail_block'),
    url(r'^kommentti/(?P<comment_id>\d+)/poista/$',
        comment_by_pk(check_perm(CanRemoveComment)(views.RemoveCommentView.as_view())),
        name='remove_comment'),
    url(r'^kommentti/(?P<comment_id>\d+)/muokkaa/$',
        comment_by_pk(check_perm(CanEditComment)(views.EditCommentView.as_view())),
        name='edit_comment'),
    url(r'^(?P<comment_id>\d+)/peru/$',
        comment_by_pk(check_perm(CanCancelVote)(views.RemoveCommentVoteView.as_view())),
        name='cancel_vote'),
]

# Comments
urlpatterns += decorated_patterns(
    '', combo(conv_by_pk, check_perm(CanCommentConversation)),
    url(r'^(?P<conversation_id>\d+)/kommentoi/$', views.PostCommentView.as_view(),
        name='post_comment'),
    url(r'^(?P<conversation_id>\d+)/vastaa/(?P<comment_id>\d+)/$',
        views.PostResponseView.as_view(),
        name='post_response'),
)

# Votes
urlpatterns += decorated_patterns(
    '', combo(comment_by_pk, check_perm(CanVoteComment)),
    url(r'^(?P<comment_id>\d+)/kannata/$',
        views.VoteCommentView.as_view(choice=Vote.VOTE_UP), name='comment_vote_up'),
    url(r'^(?P<comment_id>\d+)/vastusta/$',
        views.VoteCommentView.as_view(choice=Vote.VOTE_DOWN), name='comment_vote_down')
)
