from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ModulesConfig(AppConfig):
    name = 'djangocms_modules'
    verbose_name = _('django CMS Modules')

    def ready(self):
        import djangocms_modules.handlers  # noqa
