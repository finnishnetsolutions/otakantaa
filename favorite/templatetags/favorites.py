# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.contrib.contenttypes.models import ContentType
from libs.fimunicipality.models import Municipality
from tagging.models import Tag
from content.models import Scheme
from organization.models import Organization
from favorite.models import Favorite

register = template.Library()


def _get_favorite_schemes_by_favorite_list(model, id_list):
    schemes = None
    if model.__name__ == Tag.__name__:
        schemes = Scheme.objects.filter(tags__id__in=id_list)
    elif model.__name__ == Organization.__name__:
        schemes = Scheme.objects.filter(owners__organization_id__in=id_list,
                                        owners__approved=True)
    elif model.__name__ == Municipality.__name__:
        schemes = Scheme.objects.filter(target_municipalities__id__in=id_list)
    return schemes.public()


def _get_favorite_objects(ct, user, get_schemes=False):
    model = ct.model_class()

    obj_ids = Favorite.objects.filter(
        user=user,
        content_type=ct,
    ).values_list('object_id', flat=True)

    if model.__name__ != Scheme.__name__ and get_schemes:
        return _get_favorite_schemes_by_favorite_list(model, obj_ids)

    return model.objects.filter(pk__in=obj_ids)


@register.inclusion_tag('favorite/follow_link.html', takes_context=True)
def fav_link(context, obj=None):
    return {
        'obj': obj,
        'ct': ContentType.objects.get_for_model(obj),
        'perm': context['perm']
    }

@register.assignment_tag()
def fav_list(ct_id, user, get_schemes=False):
    ct = ContentType.objects.get(pk=ct_id)
    return _get_favorite_objects(ct, user, get_schemes).distinct()

@register.assignment_tag()
def fav_get_ct_id(natural_key):
    return ContentType.objects.get_by_natural_key(*natural_key.split('.')).pk