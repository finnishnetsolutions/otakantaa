$(function() {
    /* Code based on https://github.com/timmyomahony/django-charsleft-widget */

    $.fn.charsLeft = function(options) {

        var defaults = {
            'source': 'textarea',
            'dest': '.count',
            'maxlength': 500,
            'infoText': 'characters left',
        };

        var options = $.extend(defaults, options);

        var calculate = function (source, dest, maxlength) {
            var remaining = maxlength - source.val().length;
            dest.html(remaining);

            if (remaining < 1) {
                var text = source.val().substr(0, maxlength);
                source.val(text);
            }
        };

        this.each(function (i, el) {

            var source = $(this).find(options.source);

            $("<p class=\"brand-dark-grey\">" +
            "<span class=\"count\"></span> "+options['infoText']+"" +
            "</p>").insertAfter(source);

            var maxlength = options.maxlength;
            var dest = $(this).find(options.dest);

            // calculate the remaining chars on first load
            calculate(source, dest, maxlength);
            source.keyup(function () {
                calculate(source, dest, maxlength);
            });
            source.change(function () {
                calculate(source, dest, maxlength);
            });
        });
    };
});
