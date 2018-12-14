# -*- coding: utf-8 -*-
import copy
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.conf.urls import url
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.translation import get_language_from_request, ugettext_lazy as _
from django.views.generic import ListView

from cms import operations
from cms.exceptions import PluginLimitReached
from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.plugins import (
    copy_plugins_to_placeholder,
    get_bound_plugins,
    has_reached_plugin_limit,
    reorder_plugins,
)
from cms.utils.urlutils import admin_reverse

from .forms import AddModuleForm, CreateModuleForm, NewModuleForm
from .models import Category, ModulePlugin


def post_add_plugin(operation, **kwargs):
    from djangocms_history.actions import ADD_PLUGIN
    from djangocms_history.helpers import get_plugin_data
    from djangocms_history.models import dump_json

    module_plugin = kwargs['plugin']
    descendants = module_plugin.get_descendants()
    descendants_bound = get_bound_plugins(descendants)

    # Extend the recorded added plugins to include any nested plugin
    action = operation.actions.only('post_action_data').get(action=ADD_PLUGIN, order=1)
    post_data = json.loads(action.post_action_data)
    post_data['plugins'].extend(get_plugin_data(plugin) for plugin in descendants_bound)
    action.post_action_data = dump_json(post_data)
    action.save(update_fields=['post_action_data'])


class Module(CMSPluginBase):
    name = _('Module')
    allow_children = True
    model = ModulePlugin
    render_template = "djangocms_modules/render_module.html"
    confirmation_cookie_name = 'modules_disable_confirmation'
    readonly_fields = ['module_category']
    # These are executed by the djangocms-history app
    operation_handler_callbacks = {
        'post_add_plugin': post_add_plugin,
    }

    def has_add_permission(self, request):
        return False

    def get_plugin_urls(self):
        urlpatterns = [
            url(r'^create-module/$', self.create_module_view, name='cms_create_module'),
            url(r'^add-module/(?P<module_id>[0-9]+)/$', self.add_module_view, name='cms_add_module'),
            url(r'^modules/$', self.modules_list_view, name='cms_modules_list'),
        ]
        return urlpatterns

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type == cls.__name__:
            return

        data = {
            'language': get_language_from_request(request, check_path=True),
            'plugin': plugin.pk,
        }
        endpoint = admin_reverse('cms_create_module') + '?' + urlencode(data)
        return [
            PluginMenuItem(
                _("Create Module"),
                endpoint,
                action='modal',
                attributes={
                    'icon': 'modules'
                }
            )
        ]

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        data = {
            'language': get_language_from_request(request, check_path=True),
            'placeholder': placeholder.pk,
        }
        endpoint = admin_reverse('cms_create_module') + '?' + urlencode(data)
        return [
            PluginMenuItem(
                _("Create Module"),
                endpoint,
                action='modal',
                attributes={
                    'icon': 'modules'
                }
            )
        ]

    @classmethod
    def create_module_plugin(cls, name, category, plugins):
        placeholder = category.modules
        position = placeholder.get_plugins().filter(parent__isnull=True).count()
        plugin_kwargs = {
            'plugin_type': cls.__name__,
            'placeholder_id': category.modules_id,
            'language': settings.LANGUAGE_CODE,
            'position': position,
        }
        plugin = CMSPlugin.add_root(**plugin_kwargs)
        instance = cls.model(module_name=name, module_category=category)
        plugin.set_base_attr(instance)
        instance.save()
        copy_plugins_to_placeholder(
            plugins,
            placeholder=placeholder,
            language=plugin.language,
            root_plugin=plugin,
        )

    @classmethod
    def create_module_view(cls, request):
        if not request.user.is_staff:
            raise PermissionDenied

        new_form = NewModuleForm(request.GET or None)

        if new_form.is_valid():
            initial_data = new_form.cleaned_data
        else:
            initial_data = None

        if request.method == 'GET' and not new_form.is_valid():
            return HttpResponseBadRequest('Form received unexpected values')

        create_form = CreateModuleForm(request.POST or None, initial=initial_data)
        create_form.set_category_widget(request)

        if not create_form.is_valid():
            opts = cls.model._meta
            context = {
                'form': create_form,
                'has_change_permission': True,
                'opts': opts,
                'root_path': reverse('admin:index'),
                'is_popup': True,
                'app_label': opts.app_label,
                'media': (cls().media + create_form.media),
            }
            return render(request, 'djangocms_modules/create_module.html', context)

        plugins = create_form.get_plugins()

        if not plugins:
            return HttpResponseBadRequest('Plugins are required to create a module')

        name = create_form.cleaned_data['name']
        category = create_form.cleaned_data['category']

        if not category.modules.has_add_plugins_permission(request.user, plugins):
            raise PermissionDenied

        cls.create_module_plugin(name=name, category=category, plugins=plugins)
        return HttpResponse('<div><div class="messagelist"><div class="success"></div></div></div>')

    @classmethod
    def add_module_view(cls, request, module_id):
        if not request.user.is_staff:
            raise PermissionDenied

        module_plugin = get_object_or_404(cls.model, pk=module_id)

        if request.method == 'GET':
            form = AddModuleForm(request.GET)
        else:
            form = AddModuleForm(request.POST)

        if not form.is_valid():
            return HttpResponseBadRequest('Form received unexpected values')

        if request.method == 'GET':
            opts = cls.model._meta
            context = {
                'form': form,
                'has_change_permission': True,
                'opts': opts,
                'root_path': reverse('admin:index'),
                'is_popup': True,
                'app_label': opts.app_label,
                'module': module_plugin,
            }
            return render(request, 'djangocms_modules/add_module.html', context)

        language = form.cleaned_data['target_language']
        target_placeholder = form.cleaned_data.get('target_placeholder')

        if target_placeholder:
            target_plugin = None
        else:
            target_plugin = form.cleaned_data['target_plugin']
            target_placeholder = target_plugin.placeholder

        if not target_placeholder.has_add_plugin_permission(request.user, module_plugin.plugin_type):
            return HttpResponseForbidden(force_text(_('You do not have permission to add a plugin')))

        pl_admin = target_placeholder._get_attached_admin()

        if pl_admin:
            template = pl_admin.get_placeholder_template(request, target_placeholder)
        else:
            template = None

        try:
            has_reached_plugin_limit(
                target_placeholder,
                module_plugin.plugin_type,
                language=language,
                template=template,
            )
        except PluginLimitReached as er:
            return HttpResponseBadRequest(er)

        tree_order = target_placeholder.get_plugin_tree_order(
            language=language,
            parent_id=target_plugin,
        )

        m_admin = module_plugin.placeholder._get_attached_admin()

        # This is needed only because we of the operation signal requiring
        # a version of the plugin that's not been committed to the db yet.
        new_module_plugin = copy.copy(module_plugin)
        new_module_plugin.pk = None
        new_module_plugin.placeholder = target_placeholder
        new_module_plugin.parent = None
        new_module_plugin.position = len(tree_order) + 1

        operation_token = m_admin._send_pre_placeholder_operation(
            request=request,
            placeholder=target_placeholder,
            tree_order=tree_order,
            operation=operations.ADD_PLUGIN,
            plugin=new_module_plugin,
        )

        new_plugins = copy_plugins_to_placeholder(
            plugins=list(module_plugin.get_unbound_plugins()),
            placeholder=target_placeholder,
            language=language,
            root_plugin=target_plugin,
        )
        tree_order.append(new_plugins[0].pk)
        reorder_plugins(
            target_placeholder,
            parent_id=target_plugin,
            language=language,
            order=tree_order,
        )
        new_module_plugin = cls.model.objects.get(pk=new_plugins[0].pk)

        m_admin._send_post_placeholder_operation(
            request,
            operation=operations.ADD_PLUGIN,
            token=operation_token,
            plugin=new_module_plugin,
            placeholder=new_module_plugin.placeholder,
            tree_order=tree_order,
        )

        response = cls().render_close_frame(request, obj=new_module_plugin)

        if form.cleaned_data.get('disable_future_confirmation'):
            response.set_cookie(key=cls.confirmation_cookie_name, value=True)
        return response

    @classmethod
    def modules_list_view(cls, request):
        if not request.user.is_staff:
            raise PermissionDenied

        view = ListView.as_view(
            model=Category,
            context_object_name='categories',
            queryset=Category.objects.order_by('name'),
            template_name='djangocms_modules/modules_list.html',
        )
        return view(request)


plugin_pool.register_plugin(Module)
