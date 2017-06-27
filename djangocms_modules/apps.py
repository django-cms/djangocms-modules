from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ModulesConfig(AppConfig):
    name = 'djangocms_modules'
    verbose_name = _('django CMS Modules')

    def ready(self):
        import djangocms_modules.handlers #noqa
