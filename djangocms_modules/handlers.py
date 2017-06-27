import json

from django.apps import apps
from django.core.urlresolvers import resolve, Resolver404

from cms import operations
from cms.models import CMSPlugin

from .models import Category, ModulePlugin


def sync_module_category(sender, **kwargs):
    from djangocms_history.actions import (
        MOVE_IN_PLUGIN,
        MOVE_OUT_PLUGIN,
    )

    operation = kwargs['operation']
    actions = kwargs['actions']
    affected_operations = (operations.MOVE_PLUGIN, operations.PASTE_PLUGIN)

    if operation.operation_type not in affected_operations:
        return

    try:
        match = resolve(operation.origin)
    except Resolver404:
        match = None

    is_in_modules = match and match.url_name == 'cms_modules_list'

    if not is_in_modules:
        return

    if operation.operation_type == operations.PASTE_PLUGIN:
        if not operation.is_applied:
            # Nothing to do because undoing a paste deletes the plugin.
            return
        # User is redoing a paste
        action = actions[0]
        action_data = json.loads(action.post_action_data)
    elif operation.is_applied:
        # User is redoing moving a plugin out of a placeholder
        action = [action for action in actions if action.action == MOVE_IN_PLUGIN][0]
        action_data = json.loads(action.post_action_data)
    else:
        # User is undoing moving a plugin out of a placeholder
        action = [action for action in actions if action.action == MOVE_OUT_PLUGIN][0]
        action_data = json.loads(action.pre_action_data)

    placeholder = action.placeholder
    first_plugin = action_data['plugins'][0]

    if first_plugin['plugin_type'] == 'Module':
        new_category = Category.objects.get(modules=placeholder)
        root_plugin = CMSPlugin.objects.get(pk=first_plugin['pk'])
        (ModulePlugin
         .objects
         .filter(path__startswith=root_plugin.path, depth__gte=root_plugin.depth)
         .update(module_category=new_category))


if apps.is_installed('djangocms_history'):
    from djangocms_history import signals

    signals.post_operation_undo.connect(
        sync_module_category,
        dispatch_uid="undo_sync_module_category",
    )

    signals.post_operation_redo.connect(
        sync_module_category,
        dispatch_uid="redo_sync_module_category",
    )
