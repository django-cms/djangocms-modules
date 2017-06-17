# -*- coding: utf-8 -*-
from cms.api import get_page_draft
from cms.models import Placeholder
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.plugins import downcast_plugins
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .cms_plugins import BlueprintPlugin
from .models import USES_TREEBEARD


@toolbar_pool.register
class BlueprintToolbar(CMSToolbar):

    ## initialization methods to properly setup the toolbar

    def __init__(self, request, toolbar, is_current_app, app_path):
        from .settings import BLUEPRINT_PLACEHOLDER
        super(BlueprintToolbar, self).__init__(request, toolbar, is_current_app, app_path)
        # FIXME: why is this happening?
        try:
            self.blueprint, _ = Placeholder.objects.get_or_create(slot=BLUEPRINT_PLACEHOLDER)
        except Placeholder.MultipleObjectsReturned:
            self.blueprint = Placeholder.objects.filter(slot=BLUEPRINT_PLACEHOLDER).first()
        self.page = False
        self.placeholders = []
        self.statics = []

    def init_from_request(self):
        self.page = get_page_draft(self.request.current_page)

    def init_placeholders_from_request(self):
        self.placeholders = getattr(self.request, 'placeholders', [])
        self.statics = getattr(self.request, 'static_placeholders', [])

    def populate(self):
        self.init_from_request()

    def post_template_populate(self):
        self.init_placeholders_from_request()

    # end of the initialization methods

    def get_blueprint_plugins(self):
        self.populate()
        if not hasattr(self, "blueprint"):
            return []
        if USES_TREEBEARD:
            plugin_qs = self.blueprint.get_plugins().filter(depth=1).order_by("blueprintpluginmodel__category__order", "blueprintpluginmodel__order")
        else:
            plugin_qs = self.blueprint.get_plugins().filter(level=0).order_by("blueprintpluginmodel__category__order", "blueprintpluginmodel__order")
        if getattr(self.request, 'current_page', None) and self.request.current_page.application_urls:
            plugin_qs = plugin_qs.filter(blueprintpluginmodel__cms_only=False)
        return downcast_plugins(plugin_qs)

    def render_addons(self, context):
        context.push()
        context['local_toolbar'] = self
        blueprint = mark_safe(render_to_string('cms/toolbar/blueprint_static.html', context))
        context.pop()
        return [blueprint]

    def post_template_render_addons(self, context):
        """
        This method renders the markup to show the blueprint sidebar

        The blueprint sidebar is shown only if the current user has change permission on the
        current page or on any of the available placeholders or static placeholders
        """
        if BlueprintPlugin.has_apply_permissions(self.request):
            context.push()
            context['local_toolbar'] = self
            blueprint = mark_safe(render_to_string('cms/toolbar/blueprint.html', context))
            context.pop()
            return [blueprint]
        return []
