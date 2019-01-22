# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand

from djangocms_modules.models import Category


class Command(BaseCommand):
    help = 'Updates the language for each plugin in a module category'

    def handle(self, *args, **options):
        count = 0
        language = settings.LANGUAGE_CODE
        categories = Category.objects.select_related('modules')

        for category in categories.iterator():
            count += 1
            category.modules.cmsplugin_set.update(language=language)

        self.stdout.write('Successfully updated "%d" module categories.' % count)
