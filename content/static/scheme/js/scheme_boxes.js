$(function() {
    var schemeBoxesResults = $(".scheme-boxes-results");
    var schemeBoxes = $(".scheme-boxes");

    var babylongridSettings = {heightDivisor: 1}
    schemeBoxes.babylongrid(babylongridSettings);

    schemeBoxesResults.on("click", ".load-schemes-btn", function(e) {
        e.preventDefault();
        $.ajax({
            url: $(this).attr("href"),
            success: function(data) {
                schemeBoxesResults.html(data);
                schemeBoxesResults.find(".scheme-boxes").babylongrid(babylongridSettings);
            }
        });
    });
});
