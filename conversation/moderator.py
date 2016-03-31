# coding=utf-8

from __future__ import unicode_literals

from libs.moderation import moderation
from otakantaa.moderator import BaseModerator
from okmoderation.models import ContentFlag
from .models import Comment


class CommentModerator(BaseModerator):
    moderation_queue_template_name = 'comments/comment_moderation.html'
    auto_approve_unless_flagged = True
    visibility_column = 'is_public'

    def is_auto_approve(self, obj, user):
        if getattr(obj.conversation.get_parent_scheme(), 'premoderation', False) is True:
            # Pre-moderation needed - bypass BaseModerator, so it won't auto-approve
            # despite auto_approve_unless_flagged = True.
            #
            # moderation.GenericModerator may still auto approve e.g. based on user role
            return super(BaseModerator, self).is_auto_approve(obj, user)

        # premoderation not enabled - roll as usual taking auto_approve_unless_flagged
        # into account
        return super(CommentModerator, self).is_auto_approve(obj, user)

    def reject_object(self, moderated_object, moderator=None):
        scheme = moderated_object.content_object.conversation.get_parent_scheme()
        if scheme.premoderation \
                and not ContentFlag.objects.is_flagged(moderated_object.content_object):
            super(CommentModerator, self).reject_object(moderated_object, moderator)
        else:
            moderated_object.content_object.is_removed = True
            moderated_object.content_object.removed_by = moderator
            moderated_object.content_object.save()

    def approve_object(self, moderated_object, moderator=None):
        moderated_object.content_object.is_public = True
        moderated_object.content_object.save()


moderation.register(Comment, CommentModerator)
