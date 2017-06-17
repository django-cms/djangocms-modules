# -*- coding: utf-8 -*-
from __future__ import with_statement
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, Permission
from django.utils.encoding import force_text
from aldryn_blueprint.settings import BLUEPRINT_PLACEHOLDER

from cms.api import add_plugin, create_page
from cms.models.permissionmodels import PagePermission
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.static_placeholder import StaticPlaceholder
from cms.test_utils.testcases import CMSTestCase
from cms.utils import get_cms_setting
from cms.utils.compat.tests import UnittestCompatMixin
from cms.utils.plugins import downcast_plugins

from aldryn_blueprint import settings
from aldryn_blueprint.cms_plugins import BlueprintPlugin, USES_TREEBEARD
from aldryn_blueprint.models import Category, BlueprintPluginModel


class BlueprintPluginTests(CMSTestCase, UnittestCompatMixin):
    def setUp(self):
        self.super_user = self._create_user("test", True, True)

        self._login_context = self.login_user_context(self.super_user)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)

    def create_plugin_structure(self):
        placeholder = Placeholder(slot=u"some_slot")
        placeholder.save()  # a good idea, if not strictly necessary

        # plugin in placeholder
        plugin_1 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"01")
        plugin_1.save()

        # IMPORTANT: plugins must be reloaded, before they can be assigned
        # as a parent. Otherwise, the MPTT structure doesn't seem to rebuild
        # properly.

        # child of plugin_1
        plugin_2 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"02", target=plugin_1
        )
        plugin_2.save()

        # create a second child of plugin_1
        plugin_3 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"03", target=plugin_1,
        )
        plugin_3.save()

        # child of plugin_2
        plugin_4 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"04", target=plugin_2,
        )
        plugin_4.save()

        # create a second root plugin
        plugin_5 = add_plugin(placeholder, u"TextPlugin", u"en",
                              # force this to first-child, to make the tree more challenging
                              position='first-child',
                              body=u"05",
        )
        plugin_5.save()

        # child of plugin_5
        plugin_6 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"06", target=plugin_5,
        )
        plugin_6.save()

        # child of plugin_6
        plugin_7 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"07", target=plugin_5,
        )
        plugin_7.save()

        # create a third root plugin
        plugin_8 = add_plugin(placeholder, u"TextPlugin", u"en",
                              # force this to first-child, to make the tree more challenging
                              position='first-child',
                              body=u"08",
        )
        plugin_8.save()

        plugins = plugin_1, plugin_2, plugin_3, plugin_4, plugin_5, plugin_6, plugin_7, plugin_8
        return plugins

    def _create_blueprint(self, plugin=None, placeholder=None):
        if plugin:
            post_data = {'plugin_id': plugin.pk}
        if placeholder:
            post_data = {'placeholder_id': placeholder.pk}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'edit-plugin')
        return blueprint

    def _get_plugins(self, originals):
        """
        gather original and blueprint plugins, downcast to actual instances
        plugins can't be ordered by tree, left and right as they are all in the
        same tree now. position and parent remains the same, though
        """
        blueprint_placeholder = Placeholder.objects.get(slot=settings.BLUEPRINT_PLACEHOLDER)
        if USES_TREEBEARD:
            blueprint_plugins = CMSPlugin.objects.filter(placeholder_id=blueprint_placeholder.pk)
            copied_plugins = originals
        else:
            blueprint_plugins = CMSPlugin.objects.filter(placeholder_id=blueprint_placeholder.pk)
            copied_plugins = originals
        concrete = downcast_plugins(blueprint_plugins)
        copied_concrete = downcast_plugins(copied_plugins)

        return concrete, copied_concrete

    def _get_target_data(self):
        blueprint_placeholder = Placeholder.objects.get(slot=settings.BLUEPRINT_PLACEHOLDER)
        target_placeholder, _ = Placeholder.objects.get_or_create(slot='whatever')
        source_plugin = blueprint_placeholder.get_plugins().get(plugin_type='BlueprintPlugin')

        return blueprint_placeholder, target_placeholder, source_plugin

    def _get_static_data(self):
        blueprint_placeholder = Placeholder.objects.get(slot=settings.BLUEPRINT_PLACEHOLDER)
        target_placeholder, _ = StaticPlaceholder.objects.get_or_create(name='whatever_static   ')
        source_plugin = blueprint_placeholder.get_plugins().get(plugin_type='BlueprintPlugin')

        return blueprint_placeholder, target_placeholder, source_plugin

    def _permission_testing(self, page, static=False):

        # Superuser can edit and delete
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertContains(response, 'class="cms-blueprint-edit"')
        self.assertContains(response, 'class="cms-blueprint-delete"')

        # Useless user can't do anything
        useless_user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(useless_user):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertNotContains(response, 'class="cms-blueprint-edit"')
        self.assertNotContains(response, 'class="cms-blueprint-delete"')

        # Edit user with no permission on the page can't edit plugins
        edit_user = self._create_user(
            "staff_edit",
            is_staff=True,
            is_superuser=False,
            add_default_permissions=True
        )
        with self.login_user_context(edit_user):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        if static:
            # plugin toolbar is not shown as the user does not have permissions on static placeholders
            self.assertNotContains(response, 'class="cms-blueprint js-cms-blueprint"')
        else:
            # plugin toolbar is shown
            self.assertContains(response, 'class="cms-blueprint js-cms-blueprint"')
            # no plugin can be modified
            self.assertNotContains(response, 'class="cms-blueprint-edit"')
            self.assertNotContains(response, 'class="cms-blueprint-delete"')

        # Adding the permission on the page and to edit blueprints
        PagePermission.objects.create(user=edit_user, can_change=True, can_view=True, page=page)
        edit_user.user_permissions.add(Permission.objects.get(codename='change_blueprintpluginmodel'))
        edit_user.user_permissions.add(Permission.objects.get(codename='change_staticplaceholder'))
        with self.login_user_context(edit_user):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        # blueprint sideframe is shown for both static and normal placeholder page
        self.assertContains(response, 'class="cms-blueprint js-cms-blueprint"')
        self.assertContains(response, 'class="cms-blueprint-edit"')
        self.assertNotContains(response, 'class="cms-blueprint-delete"')

        # Delete user can only delete the current plugin
        delete_user = self._create_user(
            "staff_delete",
            is_staff=True,
            is_superuser=False,
            add_default_permissions=True
        )
        delete_user.user_permissions.add(Permission.objects.get(codename='delete_blueprintpluginmodel'))
        PagePermission.objects.create(user=delete_user, can_change=True, can_view=True, page=page)
        with self.login_user_context(delete_user):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertNotContains(response, 'class="cms-blueprint-edit"')
        self.assertContains(response, 'class="cms-blueprint-delete"')

    def test_blueprint_create_errors(self):
        originals = self.create_plugin_structure()  # nopyflakes

        post_data = {}
        request = self.get_request(path='/en/', post_data=post_data)
        request.user = AnonymousUser()
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertContains(response, 'not enough privileges', status_code=403)

        post_data = {}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertContains(response, 'plugin_id or placeholder_id ', status_code=400)

        post_data = {'plugin_id': 999999}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertContains(response, 'plugin with id', status_code=400)

        post_data = {'placeholder_id': 999999}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertContains(response, 'placeholder with id', status_code=400)

    def test_blueprint_copy_one_plugin(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[-1])  # nopyflakes

        plugins = CMSPlugin.objects.all()
        # 8 plugins + 1 blueprint + 1 copied + blueprint wrapper plugin
        self.assertEqual(plugins.count(), len(originals) + 3)
        concrete = downcast_plugins(plugins)
        self.assertEqual(originals[-1].body, concrete[-1].body)
        # copied plugins are two level deeper (blueprint  + blueprint wrapper plugin)
        if USES_TREEBEARD:
            self.assertEqual(originals[-1].depth, concrete[-1].depth - 2)
        else:
            self.assertEqual(originals[-1].level, concrete[-1].level - 2)

    def test_blueprint_copy_root_plugin(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[0])  # nopyflakes

        if USES_TREEBEARD:
            blueprint_plugins, copied_plugins = self._get_plugins(originals[0].get_tree(originals[0]))
        else:
            blueprint_plugins, copied_plugins = self._get_plugins(originals[0].get_descendants(include_self=True))

        # original plugins + blueprint plugin + blueprint wrapper plugin
        self.assertEqual(len(blueprint_plugins), len(copied_plugins) + 2)
        for index, plugin in enumerate(copied_plugins):
            if index > 0:  # skip the first one which is blueprint wrapper plugin
                # same body (means same order)
                self.assertEqual(plugin.body, blueprint_plugins[index + 2].body)
                # copied plugins are two level deeper (blueprint  + blueprint wrapper plugin)
                if USES_TREEBEARD:
                    self.assertEqual(plugin.depth, blueprint_plugins[index + 2].depth - 2)
                else:
                    self.assertEqual(plugin.level, blueprint_plugins[index + 2].level - 2)

    def test_blueprint_copy_empty_placeholder(self):
        placeholder, _ = Placeholder.objects.get_or_create(slot=u"empty_slot")

        post_data = {'placeholder_id': placeholder.pk}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.create_blueprint(request)
        self.assertContains(response, 'no plugins to create blueprint from', status_code=400)

    def test_blueprint_copy_placeholder(self):
        originals = self.create_plugin_structure()  # nopyflakes
        placeholder = Placeholder.objects.get(slot=u"some_slot")

        blueprint = self._create_blueprint(placeholder=placeholder)  # nopyflakes

        blueprint_plugins, copied_plugins = self._get_plugins(CMSPlugin.objects.filter(placeholder_id=placeholder.pk))

        # original plugins + blueprint plugin + blueprint wrapper plugin
        self.assertEqual(len(blueprint_plugins), len(copied_plugins) + 2)
        for index, plugin in enumerate(copied_plugins):
            if index > 0:  # skip the first one which is blueprint wrapper plugin
                # same body (means same order)
                self.assertEqual(plugin.body, blueprint_plugins[index + 2].body)
                # copied plugins are one level deeper
                if USES_TREEBEARD:
                    self.assertEqual(plugin.depth, blueprint_plugins[index + 2].depth - 2)
                else:
                    self.assertEqual(plugin.level, blueprint_plugins[index + 2].level - 2)

    def test_blueprint_create_from_blueprint(self):
        """
        Test that creating a blueprint out of an applied blueprint
        (represented by a BlueprintWrapperPlugin) does not recreate a wrapping
        BlueprintWrapperPlugin but uses the existing one.
        """
        originals = self.create_plugin_structure()

        self._create_blueprint(plugin=originals[-1])
        blueprint = BlueprintPluginModel.objects.all().first()

        if USES_TREEBEARD:
            # we get the *children* of the current
            wrapper = blueprint.get_children().first()
        else:
            wrapper = blueprint.get_descendants(include_self=False).first()
        self.assertEqual(CMSPlugin.objects.filter(plugin_type='BlueprintWrapperPlugin').count(), 1)

        self._create_blueprint(plugin=wrapper)

        self.assertEqual(CMSPlugin.objects.filter(plugin_type='BlueprintWrapperPlugin').count(), 2)

    def test_blueprint_apply_errors(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[-1])

        blueprint_placeholder, target_placeholder, source_plugin = self._get_target_data()
        target_language = 'fr'

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
        }
        request = self.get_request(path='/en/', post_data=post_data)
        request.user = AnonymousUser()
        blueprint = BlueprintPlugin()
        response = blueprint.apply_blueprint(request)
        self.assertContains(response, 'You do not have permission to add a plugin', status_code=403)

        post_data = {}
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.apply_blueprint(request)
        self.assertContains(response, 'source_plugin_id, target_placeholder_id or target_language ', status_code=400)

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': 'kl',
            'plugin_id': source_plugin.pk,
        }
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.apply_blueprint(request)
        self.assertContains(response, 'Language must be set to a supported language', status_code=400)

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': target_language,
            'plugin_id': 99999,
        }
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.apply_blueprint(request)
        self.assertContains(response, 'plugin with id', status_code=400)

        post_data = {
            'placeholder_id': 99999,
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
        }
        request = self.get_request(path='/en/', post_data=post_data)
        blueprint = BlueprintPlugin()
        response = blueprint.apply_blueprint(request)
        self.assertContains(response, 'placeholder with id', status_code=400)

    def test_blueprint_apply_one_root(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[-1])

        blueprint_placeholder, target_placeholder, source_plugin = self._get_target_data()

        target_language = 'fr'

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
        }

        request = self.get_request(path='/en/', post_data=post_data)
        response = blueprint.apply_blueprint(request)  # nopyflakes

        blueprint_plugins, copied_plugins = self._get_plugins(target_placeholder.get_plugins())

        # only the contained plugin is copied back + blueprint wrapper plugin
        self.assertEqual(len(copied_plugins), 2)
        self.assertEqual(copied_plugins[1].body, originals[-1].body)
        # first plugin in the placeholder, so depth is one
        if USES_TREEBEARD:
            self.assertEqual(copied_plugins[1].depth, 2)
        else:
            self.assertEqual(copied_plugins[1].level, 1)
        self.assertEqual(copied_plugins[1].language, 'fr')

    def test_blueprint_apply_one_sub(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[-1])

        blueprint_placeholder, target_placeholder, source_plugin = self._get_target_data()
        target_language = 'fr'
        target_plugin = add_plugin(target_placeholder, u"TextPlugin",
                                   target_language, body=u"target plugin")
        target_plugin.save()

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
            'plugin_parent': target_plugin.pk,
        }

        request = self.get_request(path='/en/', post_data=post_data)
        response = blueprint.apply_blueprint(request)  # nopyflakes

        blueprint_plugins, copied_plugins = self._get_plugins(target_placeholder.get_plugins())

        # the contained plugin is copied back + one existing + blueprint wrapper plugin
        self.assertEqual(len(copied_plugins), 3)
        self.assertEqual(copied_plugins[2].body, originals[-1].body)
        # the copied plugin is contained in another plugin
        if USES_TREEBEARD:
            self.assertEqual(copied_plugins[2].depth, 2)
        else:
            self.assertEqual(copied_plugins[2].level, 1)
        self.assertEqual(copied_plugins[2].language, 'fr')

    def test_blueprint_apply_one_no_placeholder(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[-1])

        blueprint_placeholder, target_placeholder, source_plugin = self._get_target_data()
        target_language = 'fr'
        target_plugin = add_plugin(target_placeholder, u"TextPlugin",
                                   target_language, body=u"target plugin")
        target_plugin.save()

        post_data = {
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
            'target_plugin_id': target_plugin.pk,
        }

        request = self.get_request(path='/en/', post_data=post_data)
        response = blueprint.apply_blueprint(request)  # nopyflakes
        blueprint_plugins, copied_plugins = self._get_plugins(target_placeholder.get_plugins())

        # the contained plugin is copied back + one existing + blueprint wrapper plugin
        self.assertEqual(len(copied_plugins), 3)
        self.assertEqual(copied_plugins[2].body, originals[-1].body)
        # the copied plugin is contained in another plugin
        if USES_TREEBEARD:
            self.assertEqual(copied_plugins[2].depth, 2)
        else:
            self.assertEqual(copied_plugins[2].level, 1)
        self.assertEqual(copied_plugins[2].language, 'fr')

    def test_blueprint_apply_tree(self):
        originals = self.create_plugin_structure()

        blueprint = self._create_blueprint(plugin=originals[0])

        blueprint_placeholder, target_placeholder, source_plugin = self._get_target_data()
        target_language = 'fr'
        target_plugin = add_plugin(target_placeholder, u"TextPlugin",
                                   target_language, body=u"target plugin")
        target_plugin.save()

        post_data = {
            'placeholder_id': target_placeholder.pk,
            'plugin_language': target_language,
            'plugin_id': source_plugin.pk,
            'plugin_parent': target_plugin.pk,
        }

        request = self.get_request(path='/en/', post_data=post_data)
        response = blueprint.apply_blueprint(request)  # nopyflakes

        blueprint_plugins, copied_plugins = self._get_plugins(target_placeholder.get_plugins())

        # the contained plugins (4) are copied back + one existing + blueprint wrapper plugin
        self.assertEqual(len(copied_plugins), 6)
        for index, plugin in enumerate(copied_plugins):
            # skipping the first two (first is different from the two sets, second one being the wrapper)
            if index > 1:
                # same body (means same order)
                self.assertEqual(plugin.body, blueprint_plugins[index].body)
                # copied plugins are one level shallower
                if USES_TREEBEARD:
                    self.assertEqual(plugin.depth, blueprint_plugins[index].depth - 1)
                else:
                    self.assertEqual(plugin.level, blueprint_plugins[index].level - 1)

    def test_blueprint_permissions_rendering(self):
        """
        Test blueprint toolbar user permissions rendering
        """

        originals = self.create_plugin_structure()
        self._create_blueprint(plugin=originals[0])

        page = create_page("toolbar-page", "static_template.html", "en", published=True)

        self._permission_testing(page, False)

    def test_blueprint_permissions_rendering_static_placeholders(self):
        """
        Test blueprint toolbar user permissions rendering on a page with static placeholders only
        """

        originals = self.create_plugin_structure()
        self._create_blueprint(plugin=originals[0])

        page_static = create_page("toolbar-page-2", "static_only.html", "en", published=True)

        self._permission_testing(page_static, True)

    def test_blueprint_multiple_placeholders(self):
        """
        Test what happens with multiple blueprint placeholders
        """
        originals = self.create_plugin_structure()
        Placeholder.objects.create(slot=BLUEPRINT_PLACEHOLDER)
        Placeholder.objects.create(slot=BLUEPRINT_PLACEHOLDER)

        create_page("toolbar-page", "page.html", "en", published=True)
        self.assertEqual(Placeholder.objects.filter(slot=BLUEPRINT_PLACEHOLDER).count(), 2)

        superuser = self.get_superuser()

        # check that the toolbar is displayed correctly
        with self.login_user_context(superuser):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertContains(response, 'class="cms-blueprint js-cms-blueprint"')

        # blueprint is created
        self._create_blueprint(plugin=originals[0])
        self.assertEqual(BlueprintPluginModel.objects.count(), 1)

        # check that the toolbar is displayed correctly and it contains at least one blueprint
        with self.login_user_context(superuser):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertContains(response, 'class="cms-blueprint-delete"')


class BlueprintAdminTests(CMSTestCase, UnittestCompatMixin):

    def test_admin_category(self):
        admin.autodiscover()
        category_admin = admin.site._registry[Category]
        media = force_text(category_admin.media)
        self.assertTrue('language_tabs.css' in media)
        self.assertTrue('list-sortable.js' in media)
        self.assertTrue('sortable.css' in media)

    def test_admin_blueprint(self):
        admin.autodiscover()
        blueprint_admin = admin.site._registry[BlueprintPluginModel]
        request = self.get_request('/')
        request.user = self.get_superuser()
        change_form = blueprint_admin.add_view(request)
        self.assertContains(change_form, '<select id="id_category" name="category">')
        self.assertContains(change_form, '<div class="parler-language-tabs">')
