# coding=utf-8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from actions.models import Action
from conversation.models import Comment
from okmessages.models import Delivery
from okmoderation.models import ContentFlag

# possible options
# label
# model
# action_type
# role
# action_subtype
# group
#

NOTIFICATION_OPTIONS = (
    {
        'label': _("Joku kommentoi hankettasi"),
        'model': Comment,
        'action_type': Action.TYPE_CREATED,
        'role': Action.ROLE_CONTENT_OWNER,
        'action_subtype': '',
        'group': Action.GROUP_ALL,
    }, {
        'label': _("Joku kommentoi seuraamaasi hanketta"),
        'model': Comment,
        'action_type': Action.TYPE_CREATED,
        'role': Action.ROLE_CONTENT_FOLLOWER,
        'action_subtype': '',
        'group': Action.GROUP_ALL,
    }, {
        'label': _("Sinulle on saapunut uusi viesti"),
        'model': Delivery,
        'action_type': Action.TYPE_CREATED,
        'role': Action.ROLE_CONTENT_OWNER,
        'action_subtype': '',
        'group': Action.GROUP_ALL,
    }
)

"""
 ,{
    'label': _("Sisältöä ilmoitetaan asiattomaksi"),
    'model': ContentFlag,
    'action_type': Action.TYPE_CREATED,
    'role': Action.ROLE_MODERATOR,
    'action_subtype': '',
    'group': Action.GROUP_MODERATORS,
},
"""
