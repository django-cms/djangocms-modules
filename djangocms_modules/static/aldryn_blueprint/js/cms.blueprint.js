/*##################################################|*/
/* #CMS# */
/* jshint camelcase: false */
(function ($) {
    'use strict';

    // CMS.$ will be passed for $
    $(document).ready(function () {
        /**
         * Blueprint
         * Adds drag & droppable template system
         *
         * @requires CMS.API.Toolbar.getSettings
         * @requires CMS.API.Toolbar.setSettings
         * @requires CMS.API.Toolbar.openMessage
         * @requires CMS.API.Toolbar.showError
         * @requires CMS.API.locked
         * @requires CMS.config
         */
        CMS.Blueprint = new CMS.Class({

            options: {
                'lang': {
                    'drop': 'Drop Here',
                    'add': 'Click to drag content',
                    'edit': 'edit',
                    'delete': 'delete'
                }
            },

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;

                this.wrapper = $('.cms-blueprint');
                this.trigger = $('.js-cms-blueprint-trigger');
                this.container = $('.cms-blueprint-container');
                this.size = 250;
                this.speed = 200;
                this.template = '<div class="cms-blueprint-dropshadow">' + this.options.lang.drop + '</div>';
                this.settings = {};
                this.initSettings = CMS.API.Toolbar.getSettings();
                this.accordionTriggers = this.wrapper.find('.cms-blueprint-accordion-trigger');
                this.accordionContainers = this.wrapper.find('.cms-blueprint-accordion-container');
                this.plugins = this._getPlugins();
                this.loader = this.wrapper.find('.cms-blueprint-loader');

                // automatically open the frame if initial state is set to open
                if (this.trigger.length && (this.wrapper.data('state') === 'open' || this.initSettings.blueprint)) {
                    this.show(1);
                }

                // start
                this._setup();
            },

            _setup: function () {
                var that = this;

                this._events();

                // check if empty and cancel
                if (this.container.find('li.empty').length) {
                    return false;
                }

                // initially allow dragging
                this._blueprintDraggable();

                // loop over all entries
                this.container.find('li').each(function (index, item) {
                    that._menu($(item));
                });

                // handle content elements
                this._contentHelper();

                // set correct visible items
                this._setAccordion();
            },

            _events: function () {
                var that = this;

                // show and hide the bar
                this.trigger.on('click', function (e) {
                    e.preventDefault();
                    if (that.wrapper.data('state') === 'closed') {
                        that.show();
                    } else {
                        that.hide();
                    }
                });

                // attach events to accordion triggers
                this.accordionTriggers.on('click', function () {
                    that._loadAccordion($(this));
                });
            },

            _contentHelper: function () {
                var that = this;
                var placeholders = $('.cms_placeholder');
                var template = $(this.template);
                // prepare temokate
                template.text(this.options.lang.add).attr('class', 'cms-blueprint-dropshadow-open');
                // attach events
                template.on('click', function () {
                    that.show();
                });
                // check if sidebar is shown on load
                if (this.wrapper.data('state') === 'open') {
                    template.hide();
                }
                // inject
                placeholders.after(template);
            },

            show: function (speed) {
                var that = this;

                this.wrapper.animate({
                    'right': this.size - 1
                }, speed || this.speed);

                // set correct height
                this.container.css('height', $(window).height() + 1);

                this._placeholders('show');
                this._droppable($('.cms-blueprint-dropshadow'));
                $('.cms-blueprint-dropshadow').show();
                $('.cms-blueprint-dropshadow-open').hide();

                // save the current state
                this.wrapper.data('state', 'open');
                this.settings.blueprint = true;
                CMS.API.Toolbar.setSettings(this.settings);

                // add active class
                this.wrapper.addClass('cms-blueprint-open');

                // we need an ugly setTimeout until plugin.data() is ready
                setTimeout(function () {
                    // when opening, we need to alter the content structure for drag&drop
                    that._addContentDragging();
                }, 100);
            },

            hide: function (speed) {
                this.wrapper.animate({
                    'right': '-1px'
                }, speed || this.speed);

                this._placeholders('hide');
                $('.cms-blueprint-dropshadow').hide();
                $('.cms-blueprint-dropshadow-open').show();

                // save the current state
                this.wrapper.data('state', 'closed');
                this.settings.blueprint = false;
                CMS.API.Toolbar.setSettings(this.settings);

                // remove active class
                this.wrapper.removeClass('cms-blueprint-open');

                // remove the drag&drop content structure
                this._removeDragging();
            },

            _placeholders: function (state) {
                var template = $(this.template).clone().addClass('cms-blueprint-droppable');
                var placeholders = $('.cms_placeholder');
                var siblings = placeholders.siblings('.cms_plugin').filter(function () {
                    return $(this).attr('class').match(/cms_plugin-[\d]+/);
                });

                // triggered when drag stopped
                if (state === 'update') {
                    $('.cms-blueprint-droppable').remove();
                    // is per default hidden
                    template.show();
                }

                // hide is triggered when closing the blueprint sidebar
                if (state === 'hide') {
                    $('.cms-blueprint-dropshadow').remove();
                } else {
                    placeholders.after(template.clone());
                    siblings.after(template.clone());
                    // reinitialize droppable area
                    this._droppable($('.cms-blueprint-dropshadow'));
                }
            },

            _blueprintDraggable: function () {
                // add dragging
                $('.cms-blueprint-templates > li').draggable({
                    'helper': 'clone',
                    'scroll': 'true'
                });

                this._droppable($('.cms-blueprint-dropshadow'));
            },

            _droppable: function (element) {
                var that = this;

                // add dropping
                element.droppable({
                    'hoverClass': 'cms-blueprint-dropshadow-active',
                    'tolerance': 'pointer',
                    'drop': function (ui, el) {
                        if (el.draggable.hasClass('cms_plugin-blueprint-draggable')) {
                            that._contentDroppable(ui, el);
                        } else {
                            that._blueprintDroppable(ui, el);
                        }
                    }
                });
            },

            _blueprintDroppable: function (ui, el) {
                var droppable = $(ui.target);
                var target = droppable.siblings('.cms_placeholder').attr('class');
                var targetPlaceholderID = parseInt(target.match(/\d+/g));
                var targetPluginID = null;
                var blueprint = parseInt(el.draggable.data('id'));

                this.loader.removeClass('hidden');

                // determine if plugin is available
                var plugin = $(ui.target).prev('.cms_plugin').attr('class');
                if (plugin) {
                    targetPluginID = parseInt(plugin.match(/\d+/g));
                    targetPlaceholderID = null;
                }

                // proceed with ajax
                this._addBlueprint(blueprint, targetPlaceholderID, targetPluginID);
            },

            _contentDroppable: function (ui, el) {
                var that = this;
                var timeout = 100;
                var dropzone = $(ui.target);
                var placeholder = dropzone.prevAll('.cms_placeholder');
                var placeholderSettings = placeholder.data().settings;
                var plugin = el.draggable;
                var pluginSettings = plugin.data().settings;

                // update position for recalculation
                dropzone.after(plugin);

                // we need a timeout until element is moved to the placeholder
                setTimeout(function () {
                    // prepare the order
                    var order = [];
                    // get the placeholder id
                    placeholder.nextAll('.cms_plugin').each(function () {
                        order.push($(this).data().settings.plugin_id);
                    });
                    // prepare the data
                    var data = {
                        'placeholder_id': placeholderSettings.placeholder_id,
                        'plugin_id': pluginSettings.plugin_id,
                        'plugin_parent': '', // pluginSettings.plugin_parent should be empty
                        'plugin_language': pluginSettings.page_language,
                        'plugin_order': order,
                        'csrfmiddlewaretoken': CMS.config.csrf
                    };

                    that._moveBlueprint(data, pluginSettings.urls.move_plugin, plugin);
                }, timeout);
            },

            _addBlueprint: function (blueprint, targetPlaceholder, targetPlugin) {
                var that = this;
                var settings = $('.cms_plugin-' + blueprint).data().settings;

                var data = {
                    // needs to be the plugin
                    'target_plugin_id': targetPlugin,
                    'plugin_language': settings.page_language || settings.plugin_language,
                    'placeholder_id': targetPlaceholder,
                    'plugin_id': settings.plugin_id || '',
                    'csrfmiddlewaretoken': CMS.config.csrf
                };

                // load similar function to CMS.Plugins.copyPlugin()
                $.ajax({
                    'type': 'POST',
                    'url': settings.urls.copy_plugin,
                    'data': data,
                    'success': function () {
                        CMS.API.Toolbar.openMessage(CMS.config.lang.success);
                        // reload
                        CMS.API.Helpers.reloadBrowser();
                    },
                    'error': function (jqXHR) {
                        CMS.API.locked = false;
                        var msg = CMS.config.lang.error;
                        that.loader.addClass('hidden');
                        // trigger error
                        CMS.API.Toolbar.showError(msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText);
                    }
                });
            },

            _moveBlueprint: function (data, url, plugin) {
                var that = this;

                $.ajax({
                    'type': 'POST',
                    'url': url,
                    'data': data,
                    'success': function () {
                        plugin.addClass('cms-blueprint-active-plugin');
                        that._placeholders('update');
                        setTimeout(function () {
                            plugin.removeClass('cms-blueprint-active-plugin');
                        }, 500);
                    },
                    'error': function (jqXHR) {
                        var msg = CMS.config.lang.error + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText;
                        CMS.API.Toolbar.showError(msg, true);
                    }
                });
            },

            _menu: function (element) {
                var modal = new CMS.Modal();
                var options = element.find('.cms-blueprint-menu a');
                var settings = $('.cms_plugin-' + element.data('id')).data().settings;

                // show and hide options
                options.hide();
                element.on('mouseenter mouseleave', function () {
                    options.toggle();
                });

                // attach edit event
                options.filter('.cms-blueprint-edit').on('click', function (e) {
                    e.preventDefault();
                    modal.open(settings.urls.edit_plugin + '?language=' + settings.page_language,
                        settings.plugin_name,
                        settings.plugin_breadcrumb);
                });

                // attach delete event
                options.filter('.cms-blueprint-delete').on('click', function (e) {
                    e.preventDefault();
                    modal.open(settings.urls.delete_plugin, settings.plugin_name, settings.plugin_breadcrumb);
                });
            },

            _getPlugins: function () {
                var elements = $('.cms_plugin');

                // this version includes all root elements
                // we can specifying only using blueprint elements by .cms-blueprint-plugin-wrapper > .cms_plugin
                elements = elements.filter(function () {
                    if (!$(this).hasClass('cms_render_model') &&
                        !$(this).parent().hasClass('cms-blueprint-plugins') &&
                        !$(this).parents('.cms_plugin').length) {
                        // return only the root plugins for dragging
                        return this;
                    }
                });

                return elements;
            },

            _addContentDragging: function () {
                var modal = new CMS.Modal();
                var settings = {};
                // first lets set them to be block items
                var template = $('<div class="cms_plugin-blueprint-draggable-menu">' +
                    '   <a href="#drag" class="blueprint-drag">drag</a>' +
                    '   <a href="#edit" class="blueprint-edit">' + this.options.lang.edit + '</a>' +
                    '   <a href="#delete" class="blueprint-delete">' + this.options.lang.delete + '</a>' +
                    '</div>');

                // add edit event
                template.find('a[href="#edit"]').on('click', function (e) {
                    e.preventDefault();
                    settings = $(this).closest('.cms_plugin').data().settings;
                    modal.open(settings.urls.edit_plugin + '?language=' + settings.page_language,
                        settings.plugin_name,
                        settings.plugin_breadcrumb);
                });

                // add delete event
                template.find('a[href="#delete"]').on('click', function (e) {
                    e.preventDefault();
                    settings = $(this).closest('.cms_plugin').data().settings;
                    modal.open(settings.urls.delete_plugin, settings.plugin_name, settings.plugin_breadcrumb);
                });

                // add dragging
                // - trying looping but element is still not draggable
                this.plugins.draggable({
                    'helper': 'clone',
                    'appendTo': 'body',
                    'clone': true
                });

                this.plugins.addClass('cms_plugin-blueprint-draggable');
                this.plugins.append(template);
            },

            _removeDragging: function () {
                this.plugins.removeClass('cms_plugin-blueprint-draggable');
                this.plugins.find('.cms_plugin-blueprint-draggable-menu').remove();
                this.plugins.draggable('destroy');
            },

            _loadAccordion: function (item) {
                var that = this;
                var index = this.accordionTriggers.index(item);

                // show and hide functions
                item.toggleClass('cms-blueprint-accordion-active');
                this.accordionContainers.eq(index).slideToggle(200, function () {
                    that._updateAccordion($(this));
                });
            },

            _updateAccordion: function () {
                var that = this;
                var array = [];

                // update storage data
                this.accordionContainers.each(function () {
                    if ($(this).is(':visible')) {
                        array.push(that.accordionContainers.index(this));
                    }
                });

                this.setStorage('cms-blueprint-accordion', array.toString());
            },

            _setAccordion: function () {
                var that = this;
                var array = this.getStorage('cms-blueprint-accordion');

                if (array) {
                    $.each(array.split(','), function (index, itemIndex) {
                        that.accordionTriggers.eq(itemIndex).trigger('click');
                    });
                } else {
                    // always show first entry
                    this.accordionTriggers.eq(0).trigger('click');
                }
            },

            setStorage: function (token, value) {
                if (typeof (Storage) !== void(0)) {
                    localStorage.setItem(token, value);
                }
            },

            getStorage: function (token) {
                if (typeof (Storage) !== void(0)) {
                    return localStorage.getItem(token);
                }
            }

        });

    });
})(CMS.$);
