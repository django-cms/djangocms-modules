# -*- coding: utf-8 -*-
from distutils.version import LooseVersion

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

import cms
from cms.models import CMSPlugin
from cms.utils.compat.dj import python_2_unicode_compatible
from filer.fields.image import FilerImageField
from parler.models import TranslatableModel, TranslatedFields
from parler.managers import TranslatableManager, TranslatableQuerySet

USES_TREEBEARD = LooseVersion(cms.__version__) >= LooseVersion('3.1')

if USES_TREEBEARD:
    from treebeard.mp_tree import MP_NodeManager, MP_NodeQuerySet

    class BlueprintQuerySet(MP_NodeQuerySet, TranslatableQuerySet):
        pass

    class BlueprintManager(MP_NodeManager, TranslatableManager):
        queryset_class = BlueprintQuerySet

        def get_queryset(self):
            return self.queryset_class(self.model, using=self._db).order_by('path')
else:
    from mptt.managers import TreeManager

    class BlueprintManager(TreeManager, TranslatableManager):
        pass


@python_2_unicode_compatible
class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_(u'name'), max_length=255)
    )
    order = models.PositiveSmallIntegerField(_(u'order'), default=0, db_index=True, blank=False,
                                             null=False)

    class Meta:
        verbose_name = _(u'blueprint category')
        verbose_name_plural = _(u'blueprints categories')
        ordering = ('order',)

    def __str__(self):
        return force_text(self.safe_translation_getter('name', any_language=True))


@python_2_unicode_compatible
class BlueprintPluginModel(CMSPlugin, TranslatableModel):
    image = FilerImageField(verbose_name=_(u'image'), null=True, blank=True)
    category = models.ForeignKey(Category, verbose_name=_(u'category'), null=True, blank=True)

    translations = TranslatedFields(
        name=models.CharField(_(u'Name'), max_length=255)
    )
    order = models.PositiveSmallIntegerField(_(u'order'), default=0, db_index=True, blank=False,
                                             null=False)
    cms_only = models.BooleanField(_(u'CMS only'), default=False,
                                   help_text=_(u'Checking this, the blueprint will be available '
                                               'for django CMS pages only'))

    objects = BlueprintManager()

    class Meta:
        verbose_name = _(u'Blueprint')
        verbose_name_plural = _(u'Blueprints')
        ordering = ('order',)

    def __str__(self):
        return force_text(self.safe_translation_getter('name', any_language=True))

    @property
    def copy_url(self):
        return reverse('admin:cms_apply_blueprint',)

    def has_change_permission(self, request):
        return request.user.has_perm('%s.change_%s' % (self._meta.app_label, self._meta.model_name))
