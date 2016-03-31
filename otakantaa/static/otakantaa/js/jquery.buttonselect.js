/*global jQuery*/

(function ($) {

    "use strict";

    $.fn.buttonSelect = function (opts) {

        var defaults = {
            wrapTag: '<div class="form-control btn-group-input" />',
            groupTag: '<div class="btn-group" data-toggle="buttons" />',
            //buttonTag: '<button type="button" class="btn btn-default" />',
            labelTag: '<label class="btn btn-default">',
            checkboxInputTag: '<input type="checkbox">',
            radioInputTag: '<input type="radio">',
            activeClass: 'active',
            multiple: null,
            changeEvent: null
        };

        opts = $.extend({}, defaults, opts);

        return this.each(function () {
            var select = $(this),
                multiple = opts.multiple !== null ? opts.multiple : select.prop('multiple'),
                btnGroup = $(opts.groupTag),
                wrap = $(opts.wrapTag),
                sthSelected = $(this).find(':selected').length > 0;

            select.find('option').each(function () {
                var opt = $(this),
                    label = opt.data("html") ? opt.data("html") : opt.text(),
                    labelMethod = opt.data("html") ? "html" : "text",
                    btn = $(opts.labelTag)[labelMethod](label),
                    input = $(multiple ? opts.checkboxInputTag : opts.radioInputTag);

                btn.prepend(input);

                if($(this).prop('selected') || (!sthSelected && $(this).val() === '')) {
                    btn.addClass(opts.activeClass);
                }

                input.on('change', function () {
                    var selected = $(this).prop('checked');
                    if(multiple) {
                        opt.prop('selected', selected);
                    } else {
                        select.val(opt.val());
                    }
                    if (opts.changeEvent !== null) {
                        select.triggerHandler(opts.changeEvent);
                    }
                });

                btnGroup.append(btn);
            });

            select.before(wrap.append(btnGroup)).hide();

        });

    };

}(jQuery));
