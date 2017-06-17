# -*- coding: utf-8 -*-
import json

from django.conf.urls import patterns, url
from django.contrib.sites.models import get_current_site
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin, Placeholder
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_list, get_cms_setting
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.permissions import has_page_change_permission
from cms.utils.plugins import downcast_plugins, reorder_plugins
from cms.utils.urlutils import admin_reverse

from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from . import settings
from .models import BlueprintPluginModel, USES_TREEBEARD


class BlueprintWrapperPlugin(CMSPluginBase):
    parent_classes = ('BlueprintPlugin',)
    name = _("Blueprint wrapper")
    allow_children = True
    render_template = "cms/plugins/blueprint_wrapper.html"
plugin_pool.register_plugin(BlueprintWrapperPlugin)


class BlueprintPluginForm(TranslatableModelForm):
    class Meta:
        model = BlueprintPluginModel


class BlueprintPlugin(CMSPluginBase, TranslatableAdmin):
    name = _("Blueprint")
    allow_children = True
    model = BlueprintPluginModel
    form = BlueprintPluginForm
    change_form_template = "admin/parler/change_form.html"
    render_template = "cms/plugins/blueprint.html"
    parent_classes = [0]  # so you will not be able to add it something
    system = True

    fields = (
        'name', 'category', 'image', 'cms_only'
    )

    def has_add_permission(self, request, *args, **kwargs):
        if self.cms_plugin_instance:
            return self.cms_plugin_instance.has_change_permission(request)
        else:
            return True
    has_delete_permission = has_change_permission = has_add_permission

    def has_add_plugin_permission(self, request, placeholder):
        if placeholder.page and not placeholder.page.has_change_permission(request):
            return False
        if not placeholder.has_add_permission(request):
            return False
        return True

    @staticmethod
    def has_apply_permissions(request):
        from cms.api import can_change_page
        permissions = False
        if request.toolbar.edit_mode:
            if getattr(request, 'current_page', None):
                permissions = permissions or can_change_page(request)
            for placeholder in getattr(request, 'placeholders', []):
                permissions = permissions or placeholder.has_change_permission(request)
            for placeholder in getattr(request, 'static_placeholders', []):
                permissions = permissions or placeholder.has_change_permission(request)
        return permissions

    def get_extra_global_plugin_menu_items(self, request, plugin):
        return [
            PluginMenuItem(
                _("Create Content block"),
                admin_reverse("cms_create_blueprint"),
                data={'plugin_id': plugin.pk, 'csrfmiddlewaretoken': get_token(request)},
                action='ajax_add'
            )
        ]

    def _patch_redirect(self, request, obj, redirect):
        # override method defined in parler because the admin views structure is different
        # after editing the changeform is closed anyway, so we just return the redirect
        return redirect

    def get_extra_placeholder_menu_items(self, request, placeholder):
        return [
            PluginMenuItem(
                _("Create Content block"),
                admin_reverse("cms_create_blueprint"),
                data={'placeholder_id': placeholder.pk, 'csrfmiddlewaretoken': get_token(request)},
                action='ajax_add'
            )
        ]

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # This pushed CMSPlugin required context variables into plain parler change form context
        context.update({
            'preview': "no_preview" not in request.GET,
            'is_popup': getattr(request, 'current_page', False),
            'plugin': self.cms_plugin_instance,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        })
        return TranslatableAdmin.render_change_form(self, request, context, add, change, form_url, obj)

    def get_plugin_urls(self):
        urlpatterns = [
            url(r'^create_blueprint/$', self.create_blueprint, name='cms_create_blueprint'),
            url(r'^apply_blueprint/$', self.apply_blueprint, name='cms_apply_blueprint'),
        ]
        urlpatterns = patterns('', *urlpatterns)
        return urlpatterns

    def create_blueprint(self, request):
        from .settings import BLUEPRINT_PLACEHOLDER
        if not request.user.is_staff:
            return HttpResponseForbidden("not enough privileges")
        if 'plugin_id' not in request.POST and 'placeholder_id' not in request.POST:
            return HttpResponseBadRequest("plugin_id or placeholder_id POST parameter missing.")
        plugins = []
        # Get the current plugins
        if 'plugin_id' in request.POST:
            pk = request.POST['plugin_id']
            try:
                plugins = [CMSPlugin.objects.get(pk=pk)]
            except CMSPlugin.DoesNotExist:
                return HttpResponseBadRequest("plugin with id %s not found." % pk)
        # Get the top level plugins in the current placeholder
        if 'placeholder_id' in request.POST:
            pk = request.POST['placeholder_id']
            try:
                if USES_TREEBEARD:
                    plugins = Placeholder.objects.get(pk=pk).get_plugins().filter(depth=1)
                else:
                    plugins = Placeholder.objects.get(pk=pk).get_plugins().filter(level=0)
            except Placeholder.DoesNotExist:
                return HttpResponseBadRequest("placeholder with id %s not found." % pk)
        # FIXME: why is this happening?
        try:
            placeholder, noop = Placeholder.objects.get_or_create(slot=BLUEPRINT_PLACEHOLDER)
        except Placeholder.MultipleObjectsReturned:
            placeholder = Placeholder.objects.filter(slot=BLUEPRINT_PLACEHOLDER).first()
        language = get_language_list(get_current_site(request))[0]
        if plugins:
            # Creating the container plugin
            blueprint = BlueprintPluginModel(language=language, placeholder=placeholder,
                                             plugin_type="BlueprintPlugin")
            blueprint.save()
            wrapper = CMSPlugin(language=language, placeholder=placeholder,
                                parent=blueprint, plugin_type="BlueprintWrapperPlugin")
            wrapper.save()
            if plugins[0].plugin_type == "BlueprintWrapperPlugin":
                if USES_TREEBEARD:
                    # we get the *children* of the current
                    plugins = plugins[0].get_children()
                else:
                    plugins = plugins[0].get_descendants(include_self=False)
            # For every top level plugin all the children is selected
            # and copied to the blueprint placeholder
            # with the blueprint plugins as parent. In this way we
            # recreate the plugin structure but with a blueprint top-level plugin
            # that contains them all
            if not USES_TREEBEARD:
                plugins = reversed(plugins)
            for plugin in plugins:
                if USES_TREEBEARD:
                    children = plugin.get_tree(plugin)
                else:
                    children = plugin.get_descendants(include_self=True)
                children = list(downcast_plugins(children))
                copy_plugins_to(children, placeholder, language, parent_plugin_id=wrapper.pk)
            response = {
                'url': force_text(
                    admin_reverse("cms_page_edit_plugin", args=[blueprint.pk])),
                'delete': force_text(
                    admin_reverse("cms_page_edit_plugin", args=[blueprint.pk])),
                'breadcrumb': blueprint.get_breadcrumb(),
            }
            return HttpResponse(json.dumps(response), content_type='application/json')
        return HttpResponseBadRequest("no plugins to create blueprint from.")

    def apply_blueprint(self, request):
        target_language = request.POST.get('plugin_language', None)
        target_placeholder_id = request.POST.get('placeholder_id', None)
        target_plugin_id = request.POST.get('target_plugin_id', None)
        source_plugin_id = request.POST.get('plugin_id', None)

        target_plugin = None
        front_plugins = []
        middle_plugins = []

        # if parent_plugin is set, add the blueprint after it and not into it
        if not target_placeholder_id and target_plugin_id:
            target_plugin = CMSPlugin.objects.get(pk=target_plugin_id)
            target_placeholder_id = target_plugin.placeholder_id
        if not source_plugin_id or not target_placeholder_id or not target_language:
            return HttpResponseBadRequest("source_plugin_id, target_placeholder_id or target_language POST parameter missing.")
        if not target_language or target_language not in get_language_list():
            return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))
        try:
            plugin = CMSPlugin.objects.get(pk=source_plugin_id)
        except CMSPlugin.DoesNotExist:
            return HttpResponseBadRequest("plugin with id %s not found." % source_plugin_id)
        try:
            target_placeholder = Placeholder.objects.get(pk=target_placeholder_id)
        except Placeholder.DoesNotExist:
            return HttpResponseBadRequest("placeholder with id %s not found." % target_placeholder_id)
        if not Placeholder.objects.filter(slot=settings.BLUEPRINT_PLACEHOLDER).exists():
            return HttpResponseBadRequest("%s placeholder not found." % settings.BLUEPRINT_PLACEHOLDER)

        if not self.has_add_plugin_permission(request, target_placeholder):
            return HttpResponseForbidden(force_text(_('You do not have permission to add a plugin')))

        base_plugins = list(CMSPlugin.objects.filter(parent=None, placeholder=target_placeholder, language=target_language).order_by('position').values_list('pk', flat=True))
        # split the list of plugins so that the newsly created ones are pushed in the middle of the stack
        if target_plugin:
            front_plugins = base_plugins[:base_plugins.index(target_plugin.pk)+1]
            end_plugins = base_plugins[base_plugins.index(target_plugin.pk)+1:]
        else:
            end_plugins = base_plugins

        if USES_TREEBEARD:
            plugins = plugin.get_tree(plugin).filter(depth=2)
        else:
            plugins = plugin.get_descendants(include_self=False).filter(level=1)
        for root_plugin in plugins:
            if USES_TREEBEARD:
                children = root_plugin.get_tree(root_plugin)
            else:
                children = root_plugin.get_descendants(include_self=True)
            children = downcast_plugins(children)
            new_plugins = copy_plugins_to(children, target_placeholder, target_language, no_signals=True)
            # inserting the new plugins (only the root ones) in the middle of the plugin stack
            if USES_TREEBEARD:
                middle_plugins.extend([new_plugin.pk for new_plugin, noop in new_plugins if new_plugin.depth == 1])
            else:
                middle_plugins.extend([new_plugin.pk for new_plugin, noop in new_plugins if new_plugin.level == 0])
        # do reordering
        reorder_plugins(target_placeholder, None, target_language, front_plugins + middle_plugins + end_plugins)
        response = {
            'reload': True
        }
        return HttpResponse(json.dumps(response), content_type='application/json')
plugin_pool.register_plugin(BlueprintPlugin)
