from django.db import migrations, models

import cms.models.fields

import djangocms_modules.models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_auto_20160608_1535'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=120, verbose_name='name')),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='ModulePlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, related_name='djangocms_modules_moduleplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin', on_delete=models.CASCADE)),
                ('module_name', models.CharField(max_length=120, verbose_name='name')),
                ('module_category', models.ForeignKey(verbose_name='category', to='djangocms_modules.Category', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='ModulesPlaceholder',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('cms.placeholder',),
        ),
        migrations.AddField(
            model_name='category',
            name='modules',
            field=cms.models.fields.PlaceholderField(slotname=djangocms_modules.models._get_placeholder_slot, editable=False, to='cms.Placeholder', null=True),
        ),
    ]
