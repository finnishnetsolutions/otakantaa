# coding=utf-8

from __future__ import unicode_literals

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.template.base import render_value_in_context, TemplateSyntaxError, Node

register = template.Library()


@register.simple_tag(takes_context=True)
def render_template_to_variable(context, **kwargs):
    for variable_name, template_name in kwargs.iteritems():
        context[variable_name] = render_to_string(template_name, context_instance=context)
    return ""


@register.filter(is_safe=False)
def add_to_str(value, arg):
    """Adds the arg to the value."""
    return "{}{}".format(value, arg)


@register.filter(is_safe=False)
def og_pic_url(obj=None):
    pic_url = '{}{}'.format(settings.STATIC_URL, settings.FB_LOGO_URL)
    if obj is not None and hasattr(obj, 'picture') and obj.picture:
        if hasattr(obj, 'picture_main'):
            return obj.picture_main.url
        elif hasattr(obj, 'picture_medium'):
            return obj.picture_medium.url
    return pic_url


# copied from django 1.9
class FirstOfNode(Node):
    def __init__(self, variables, asvar=None):
        self.vars = variables
        self.asvar = asvar

    def render(self, context):
        for var in self.vars:
            value = var.resolve(context, True)
            if value:
                first = render_value_in_context(value, context)
                if self.asvar:
                    context[self.asvar] = first
                    return ''
                return first
        return ''


# copied from django 1.9 so we can use asvar
@register.tag
def okfirstof(parser, token):
    bits = token.split_contents()[1:]
    asvar = None
    if len(bits) < 1:
        raise TemplateSyntaxError("'firstof' statement requires at least one argument")

    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]
    return FirstOfNode([parser.compile_filter(bit) for bit in bits], asvar)
