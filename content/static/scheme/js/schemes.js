var animation_options = {
    duration: 400,
    easing: "swing"
};

$(function() {
    // Keep the two searches synced.
    // TODO: A better way to handle the two inputs.
    var search_text_wrap = $(".scheme-search-text");
    var compact_text = search_text_wrap.children(".compact-search-component").find("input");
    var extended_text = search_text_wrap.children(".extended-search-component").find("input");
    compact_text.change(function() {
        extended_text.val($(this).val());
    });
    extended_text.change(function() {
        compact_text.val($(this).val());
    });

    // Initial show/hide extended search components.
    if ( ! $("#id_extended_search").prop("checked")) {
        $(".extended-search-component").hide();
        $(".extended-search-components").hide();
    }
    else {
        $(".compact-search-component").hide();
        $(".extended-search-component").show();
        $(".extended-search-components").show();
    }

    // Clicking show/hide extended search components.
    $("#show-extended-search-form").click(function() {
        $("#id_extended_search").prop("checked", true);
        $(".extended-search-component").show();
        $(".extended-search-components").slideDown(animation_options);
        $(".compact-search-component").hide();
    });
    $("#hide-extended-search-form").click(function() {
        $("#id_extended_search").prop("checked", false);
        $(".extended-search-component").hide();
        $(".extended-search-components").slideUp(animation_options);
        $(".compact-search-component").show();
    });
});