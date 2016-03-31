/* global $, window*/

$(function () {

    "use strict";

    var STATUS_CODES = {
        OK: 200,
        RESET_CONTENT: 205,
        BAD_REQUEST: 400,
        NO_CONTENT: 204,
        AJAXY_REDIRECT: 231,
        AJAXY_INLINE_REDIRECT: 232
    };

    var ajaxyResponseHandler = function(wrap, returnUrl, trigger, eventName, targetMethod) {
        return function (resp, textStatus, xhr) {
            var next = null, location = null, reload = false, unknownError = false,
                noop = false;

            targetMethod = targetMethod || "html";

            if (xhr) {
                if (xhr.status === STATUS_CODES.RESET_CONTENT) {
                    reload = true;
                } else if (xhr.status === STATUS_CODES.AJAXY_REDIRECT) {
                    location = xhr.getResponseHeader('Location');
                } else if (xhr.status === STATUS_CODES.AJAXY_INLINE_REDIRECT) {
                    next = xhr.getResponseHeader('Location');
                } else if (xhr.status === STATUS_CODES.NO_CONTENT) {
                    noop = true;
                }
                if (xhr.status > STATUS_CODES.BAD_REQUEST) {
                    if ('console' in window) {
                        window.console.warn(
                            'Unpexpected error response', xhr.status, xhr.statusText
                        );
                    }
                    unknownError = true;
                }
            } else {
                if(typeof resp === "string") {
                    // Try to interpret response as json. Useful with
                    // jQuery form plugin's IE9 iframe file upload hack.
                    try {
                        resp = jQuery.parseJSON(resp);
                        if (resp.reload) {
                            reload = reload;
                        } else if (resp.location) {
                            next = resp.location;
                        }
                    } catch (e) {
                    }
                }
            }

            if (!next && returnUrl) {
                next = returnUrl;
            }

            var e = $.Event(eventName, {wrap: wrap, trigger: trigger,
                response: resp, textStatus: textStatus,
                xhr: xhr});

            trigger.trigger(e);

            if (unknownError) {
                // Failed with unexpected error code. No default behaviour.
                return;
            }

            if (noop) {
                return;
            }

            if (!e.isPropagationStopped()) {

                if (reload) {
                    window.location.reload(true);
                } else if (location) {
                    window.location.replace(location);
                } else if (next) {
                    wrap.load(next, function () {
                        wrap.trigger('ajaxyRefreshed');
                    });
                } else if (wrap) {
                    wrap[targetMethod](resp).trigger('ajaxyRefreshed');
                }
            }

            if (_.contains(["yes", 1, "true", true], trigger.data('ajaxy-remove-triggerer'))) {
                trigger.remove();
            }

            if (_.contains(["yes", 1, "true", true], trigger.data('ajaxy-remove-triggerer-wrap'))) {
                wrap.remove();
            }
        }
    };

    var ajaxySuccessHandler = function (wrap, returnUrl, trigger, targetMethod) {
        return ajaxyResponseHandler(wrap, returnUrl, trigger, 'ajaxySuccess', targetMethod);
    };

    var ajaxyErrorHandler = function (wrap, returnUrl, trigger, targetMethod) {
        return function (xhr) {
            return ajaxyResponseHandler(wrap, returnUrl, trigger, 'ajaxyError', targetMethod)(
                xhr.responseText, 'error', xhr
            );
        };
    };

    var getAjaxyTargets = function (el) {
        var target, successTarget = null, errorTarget = null, targetMethod;

        if (_.contains(["yes", 1, "true", true], el.data('ajaxy-replace-trigger'))) {
            target = el;
            targetMethod = 'replaceWith';
        } else {
            target = el.data('ajaxy-target');
            targetMethod = el.data('ajaxy-target-method') || targetMethod;
        }

        if (target) {
            target = $(target);
        } else {
            target = el.parents('.ajaxy-wrap').first();
        }

        if (el.data('ajaxy-success-target')) {
            successTarget = $(el.data('ajaxy-success-target'));
        }

        if (el.data('ajaxy-error-target')) {
            errorTarget = $(el.data('ajaxy-error-target'));
        }

        return {
            success: successTarget || target,
            error: errorTarget || target,
            // jQuery method to use on the target-element to show the ajax response
            targetMethod: targetMethod
        };
    };

    $(document).on('click', '.ajaxy-link', function (e) {
        var beforeLinkage, target, targets, method, targetMethod, confirmation,
            dialogClass, modalWrap;

        e.preventDefault();

        confirmation = $(this).data('ajaxy-confirmation');
        if (confirmation && !window.confirm(confirmation)) {
            return false;
        }

        beforeLinkage = $.Event("beforeAjaxyLinkage");

        $(this).trigger(beforeLinkage);

        if (beforeLinkage.isPropagationStopped()) {
            return false;
        }

        // HTTP method to use in the ajax request
        method = $(this).data('ajaxy-method') || "GET";

        if($(this).data('toggle') == 'ajaxy-modal') {
            dialogClass = $(this).data('modal-dialog-class') || 'modal-lg';
            modalWrap = $(
                '<div class="modal fade">' +
                '<div class="modal-dialog">' +
                '<div class="modal-content ajaxy-wrap"></div>' +
                '</div>' +
                '</div>'
            );
            modalWrap.children('.modal-dialog').addClass(dialogClass);
            target = modalWrap.find('.ajaxy-wrap');
            targets = {
                success: target,
                error: target
            };
            $('body').append(modalWrap.hide());

            modalWrap.on('hidden.bs.modal', function () {
                $(this).remove();
            });

        } else {
            targets = getAjaxyTargets($(this));
        }

        $.ajax($(this).attr('href'), {type: method})
            .done(ajaxySuccessHandler(targets.success,
                $(this).data('ajaxy-success-url'),
                $(this),
                targets.targetMethod))
            .fail(ajaxyErrorHandler(targets.error,
                $(this).data('ajaxy-error-url'),
                $(this),
                targets.targetMethod));
    });

    $(document).on('ajaxyRefreshed', '.modal-content.ajaxy-wrap', function () {
        $(this).parents('.modal').first().modal('show');
    });

    $(document).on('submit', '.ajaxy-form', function (e) {
        var form = $(this), onSuccess, onError, beforeSubmit, targets, formData;

        e.preventDefault();

        targets = getAjaxyTargets(form);

        onSuccess = ajaxySuccessHandler(targets.success,
            form.data('ajaxy-return-url'),
            form,
            targets.targetMethod);

        onError = ajaxyErrorHandler(targets.error,
            form.data('ajaxy-return-url'),
            form,
            targets.targetMethod);

        beforeSubmit = $.Event("beforeAjaxySubmit");

        form.trigger(beforeSubmit);

        if (beforeSubmit.isPropagationStopped()) {
            return false;
        }

        if(form.is('form')) {
            $(this).ajaxSubmit({success: onSuccess, error: onError});
        } else {
            formData = form.find(':input').serialize();
            $.post(form.data('ajaxy-action'), formData).done(onSuccess).fail(onError);
        }

    });

    $(document).on('ajaxyReload', '.ajaxy-wrap', function () {
        var self = $(this);
        $(this).load($(this).data('ajaxy-url'), function () {
            $(this).trigger('ajaxyRefreshed');
        });
    });

    $(document).on('click', '.ajaxy-form :input[type="submit"]', function () {
        var ajaxyForm = $(this).parents('.ajaxy-form').first();
        if (!ajaxyForm.is('form')) {
            // it's a fake form, trigger submit manually
            ajaxyForm.trigger('submit');
        }
    });

    $.ajaxyModal = function (url, opts) {
        // TODO: DRY against ajaxy-link click?
        var target, targets, dialogClass, opts = opts || {}, modalWrap = $(
            '<div class="modal fade">' +
            '<div class="modal-dialog">' +
            '<div class="modal-content ajaxy-wrap"></div>' +
            '</div>' +
            '</div>'
        );
        dialogClass = opts.dialogClass || 'modal-lg';
        modalWrap.children('.modal-dialog').addClass(dialogClass);
        target = modalWrap.find('.ajaxy-wrap');
        modalWrap.data('ajaxyWrap', target);

        $('body').append(modalWrap.hide());
        modalWrap.on('hidden.bs.modal', function () {
            $(this).remove();
        });

        $.ajax(url, {
            type: opts.method || 'GET',
            data: opts.data || null
        }).done(ajaxySuccessHandler(opts.successTarget || target,
            opts.returnUrl || null,
            opts.trigger || modalWrap))
            .fail(ajaxyErrorHandler(opts.errorTarget || opts.successTarget || target,
                opts.returnUrl || null,
                opts.trigger || modalWrap));

        return modalWrap;
    };

});

