from django import template
from django.conf import settings

from cms.utils.urlutils import admin_reverse

from ..models import Category


register = template.Library()


@register.simple_tag(takes_context=False)
def get_default_language():
    # le sigh...
    return settings.LANGUAGE_CODE


@register.simple_tag(takes_context=False)
def get_module_categories():
    return Category.objects.order_by('name')


@register.simple_tag()
def get_module_add_url(module_):
    return admin_reverse('cms_add_module', args=[module_.pk])


@register.simple_tag(takes_context=False)
def get_module_url(module_):
    return admin_reverse('cms_modules_list') + '#cms-plugin-{}'.format(module_.pk)
