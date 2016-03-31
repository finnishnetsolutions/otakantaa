from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from account.models import User


class Favorite(models.Model):

    TYPE_TAG = 'tagging.tag'
    TYPE_ORGANIZATION = 'organization.organization'
    TYPE_MUNICIPALITY = 'fimunicipality.municipality'
    TYPES = (
        TYPE_TAG,
        TYPE_ORGANIZATION,
        TYPE_MUNICIPALITY,
    )

    user = models.ForeignKey(User, related_name='favorites')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'content_type', 'object_id'), )
