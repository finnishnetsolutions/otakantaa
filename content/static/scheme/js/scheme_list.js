$(function() {
    var schemeListResults = $(".scheme-list-results");

    schemeListResults.on("click", ".load-schemes-btn", function(e) {
        e.preventDefault();
        $.ajax({
            url: $(this).attr("href"),
            success: function(data) {
                schemeListResults.html(data);
                schemeListResults.find(".scheme-boxes").babylongrid(babylongridSettings);
            }
        });
    });
});
