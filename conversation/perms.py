# coding=utf-8

from __future__ import unicode_literals

from importlib import import_module

from .conf import config

perms = import_module(config.perms_path)

CanCommentConversation = perms.CanCommentConversation
CanVoteComment = perms.CanVoteComment
CanEditComment = perms.CanEditComment
CanRemoveComment = perms.CanRemoveComment
CanCancelVote = perms.CanCancelVote
