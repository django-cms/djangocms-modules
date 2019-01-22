# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget, RelatedFieldWidgetWrapper

from cms.models import CMSPlugin, Placeholder

from .models import Category, ModulePlugin


class NewModuleForm(forms.Form):
    plugin = forms.ModelChoiceField(
        CMSPlugin.objects.exclude(plugin_type='Module'),
        required=False,
        widget=forms.HiddenInput(),
    )
    placeholder = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    language = forms.ChoiceField(
        choices=settings.LANGUAGES,
        required=True,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        if self.errors:
            return self.cleaned_data

        plugin = self.cleaned_data.get('plugin')
        placeholder = self.cleaned_data.get('placeholder')

        if not plugin and not placeholder:
            message = 'A plugin or placeholder is required to create a module'
            raise forms.ValidationError(message)

        if plugin and placeholder:
            message = 'A module can only be created from a plugin or placeholder, not both.'
            raise forms.ValidationError(message)
        return self.cleaned_data


class CreateModuleForm(NewModuleForm):

    name = forms.CharField(required=True, widget=AdminTextInputWidget)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
    )

    def set_category_widget(self, request):
        related_modeladmin = admin.site._registry.get(Category)
        dbfield = ModulePlugin._meta.get_field('module_category')
        formfield = self.fields['category']
        formfield.widget = RelatedFieldWidgetWrapper(
            formfield.widget,
            dbfield.rel if hasattr(dbfield, 'rel') else dbfield.remote_field,
            admin_site=admin.site,
            can_add_related=related_modeladmin.has_add_permission(request),
            can_change_related=related_modeladmin.has_change_permission(request),
            can_delete_related=related_modeladmin.has_delete_permission(request),
        )

    def get_plugins(self):
        plugin = self.cleaned_data.get('plugin')
        placeholder = self.cleaned_data.get('placeholder')

        if placeholder:
            language = self.cleaned_data['language']
            plugins = placeholder.get_plugins(language)
        else:
            plugins = plugin.get_tree(plugin).order_by('path')
        return list(plugins)


class AddModuleForm(forms.Form):
    target_plugin = forms.ModelChoiceField(
        CMSPlugin.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    target_language = forms.ChoiceField(
        choices=settings.LANGUAGES,
        required=True,
        widget=forms.HiddenInput(),
    )
    target_placeholder = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    disable_future_confirmation = forms.BooleanField(required=False, initial=False)

    def clean(self):
        if self.errors:
            return self.cleaned_data

        plugin = self.cleaned_data.get('target_plugin')
        placeholder = self.cleaned_data.get('target_placeholder')

        if not plugin and not placeholder:
            message = 'A plugin or placeholder is required to apply a module'
            raise forms.ValidationError(message)

        if plugin and placeholder:
            message = 'A module can only be applied to a plugin or placeholder, not both.'
            raise forms.ValidationError(message)
        return self.cleaned_data
