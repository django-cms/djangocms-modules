# -*- coding: utf-8 -*-
from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from parler.admin import TranslatableAdmin

from .models import Category, BlueprintPluginModel


class BlueprintAdminClass(SortableAdminMixin, TranslatableAdmin):
    list_filter = ('category',)


class CategoryAdminClass(SortableAdminMixin, TranslatableAdmin):
    """Any admin options you need go here"""
    enable_sorting = True

    @property
    def media(self):
        from parler.admin import _fakeRequest, _language_prepopulated_media, _language_media
        has_prepopulated = len(self.get_prepopulated_fields(_fakeRequest))
        sortable = super(CategoryAdminClass, self).media
        if has_prepopulated:
            return sortable + _language_prepopulated_media
        else:  #NOQA
            return sortable + _language_media

admin.site.register(Category, CategoryAdminClass)
admin.site.register(BlueprintPluginModel, BlueprintAdminClass)
