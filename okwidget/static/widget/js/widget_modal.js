$(function() {
    var inputs = $(".widget-modal-refreshers").find(":input");
    inputs.change(refresh_widget_preview);
});

function refresh_widget_preview() {
    var widget_modal_preview = $(".widget-modal-preview");

    // Generate url
    var widget_url = widget_modal_preview.data("widget-url");
    if (widget_url.indexOf("?") == -1) {
        widget_url += "?";
    }
    else {
        widget_url += "&";
    }
    widget_url += $(".widget-modal-refreshers").find(":input").serialize();

    // Update preview.
    $.ajax({
        url: widget_url,
        success: function(data) {
            $(".widget-modal-preview").html(data);
        }
    });

    // Update iframe code.
    var base_url = widget_modal_preview.data("base-url");
    $(".widget-modal-code").html("<iframe src='" + base_url + widget_url + "'></iframe>");
}
