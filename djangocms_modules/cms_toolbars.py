from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse


SHORTCUTS_BREAK = 'Shortcuts Break'


@toolbar_pool.register
class ModulesToolbar(CMSToolbar):
    """
    Adds a Modules menu-item into django CMS's "ADMIN" (first) menu.
    """

    class Media:
        js = ('djangocms_modules/js/dist/bundle.modules.min.js',)
        css = {
            'all': ('djangocms_modules/css/modules.css',)
        }

    @staticmethod
    def get_insert_position(admin_menu, item_name):
        """
        Ensures that there is a SHORTCUTS_BREAK and returns a position for an
        alphabetical position against all items between SHORTCUTS_BREAK, and
        the ADMINISTRATION_BREAK.
        """
        start = admin_menu.find_first(Break, identifier=SHORTCUTS_BREAK)

        if not start:
            end = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)
            admin_menu.add_break(SHORTCUTS_BREAK, position=end.index)
            start = admin_menu.find_first(Break, identifier=SHORTCUTS_BREAK)
        end = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)

        items = admin_menu.get_items()[start.index + 1: end.index]
        for idx, item in enumerate(items):
            try:
                if force_str(item_name.lower()) < force_str(item.name.lower()):
                    return idx + start.index + 1
            except AttributeError:
                # Some item types do not have a 'name' attribute.
                pass
        return end.index

    def populate(self):
        modules = _('Modules')
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        admin_menu.add_link_item(
            modules,
            url=admin_reverse('cms_modules_list'),
            position=self.get_insert_position(admin_menu, modules)
        )
