from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin

from .models import Category


class CategoryAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ['name']


admin.site.register(Category, CategoryAdmin)
