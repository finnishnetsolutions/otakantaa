$(function() {
    "use strict";

    function change_choice(event) {
        var page = 1
        if ($(this).attr('name') !== 'messages-choice') {
            page = get_active_page_nr();
        }

        var loader_obj = show_loader_icon();
        $.ajax({
            url: $("#messages-change-url").attr("href"),
            data: {
                'page': 1,
                "nayta": $(this).val(),
                "jarjestys": $("input[name=messages-sorting]:checked").val()
            }
        }).done(function(html) {
            loader_obj.hide();
            $("#messages-table-wrapper").html(html);
        });
    }

    function change_sorting(event) {
        var loader_obj = show_loader_icon();
        $.ajax({
            url: $("#messages-change-url").attr("href"),
            data: {
                'page': get_active_page_nr(),
                "nayta": $("input[name=messages-choice]:checked").val(),
                "jarjestys": $(this).val()
            }
        }).done(function(html) {
            loader_obj.hide();
            $("#messages-table-wrapper").html(html);
        });

    }

    function show_loader_icon() {
        var $ajax_loading = $("#messages-ajax-loading");
        $ajax_loading.show();
        return $ajax_loading;
    }

    function get_active_page_nr() {
        return $('ul.pagination > li.active').find('a').html();
    }


    $("input[name=messages-choice]").on('change', change_choice);
    $("input[name=messages-sorting]").on('change', change_sorting);
    $(document).on('click', 'ul.pagination > li', function(event) {
        event.preventDefault();
        event.stopPropagation();
        var url = $(this).find('a').attr('href');
        var loader_obj = show_loader_icon();
        if (url === '#') {
            loader_obj.hide();
            return false;
        }

        var data = {
            'nayta': $("input[name=messages-choice]:checked").val(),
            'jarjestys': $("input[name=messages-sorting]:checked").val()
        };

        url += "&" + $.param(data);
        $.ajax({url: url})
            .done(function(html) {
                loader_obj.hide();
                $("#messages-table-wrapper").html(html);
            });
        return false;
    });
});
