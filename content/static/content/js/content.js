/**
 * Sidebar toggling.
 */

// Determines if the user has clicked the toggle button and which state has he toggled to.
var sidebar_shown = null;

$(function() {
    $(window).resize(_.debounce(update_content_sidebar, 100));

    var sidebar_collapse = $("#content-sidebar-collapse");
    var sidebar_toggle = $(".content-sidebar-toggle");

    sidebar_toggle.click(function() {
        sidebar_shown = $("#content-sidebar-collapse").hasClass("in");
        sidebar_collapse.collapse("toggle");
        sidebar_shown = ! sidebar_shown;
    });

    sidebar_collapse.on("hidden.bs.collapse shown.bs.collapse", function() {
        $(this).removeAttr("style");
    });

    update_content_sidebar();

    $('.content-details-collapse-button').on('click', function() {
        $(this).hide();
        $(this).siblings('.content-details-collapse-button').show();
    });
});

function update_content_sidebar() {
    var window_width = $(window).width();

    // User has not toggled visibility, use the default behaviour.
    if (sidebar_shown == null) {
        if (window_width < 992) {
            // default changed on purpose
            collapse_content_sidebar("show", false);
        }
        else {
            collapse_content_sidebar("show", false);
        }
    }

    // User has toggled visibility, but the window width is 992px or above.
    else if (window_width >= 992) {
        collapse_content_sidebar("show", false);
    }

    // Window width is below 992 and user has toggled to hide the sidebar.
    else if (sidebar_shown == false) {
        collapse_content_sidebar("hide", false);
    }
}

function collapse_content_sidebar(visibility, transition) {
    transition = transition !== undefined ? transition : true;
    var sidebar_collapse = $("#content-sidebar-collapse");

    if (transition === true) {
        sidebar_collapse.collapse(visibility);
    }
    else if (transition === false) {
        sidebar_collapse.css("transition", "none");
        sidebar_collapse.collapse(visibility);
    }
}


/**
 * Moving content based on window width.
 */

$(function() {
    $(window).resize(_.debounce(update_content_location, 100));
    update_content_location();
});

function update_content_location() {
    var window_width = $(window).width();

    if (window_width < 992) {
        $("#content-details-collapse").append($(".content-maincontent"));
    }
    else {
        $(".content-contents-wrap").prepend($(".content-maincontent"));
    }
}


/**
 * Hiding and showing content details on mobile view.
 */

// Determines if the user has clicked "show details".
var details_shown = null;

$(function() {
    $(window).resize(_.debounce(update_details_visibility, 100));
    update_details_visibility();

    var details_collapse = $("#content-details-collapse");
    var show_details = $(".content-details-show").children("button");
    var hide_details = $(".content-details-hide").children("button");

    show_details.click(function() {
        details_collapse.collapse("show");
        details_shown = true;
        $(".content-details-hide").show();
        $(".content-details-show").hide();
    });
    hide_details.click(function() {
        details_collapse.collapse("hide");
        details_shown = false;
        $(".content-details-hide").hide();
        $(".content-details-show").show();
    });

    details_collapse.on("hidden.bs.collapse shown.bs.collapse", function() {
        $(this).removeAttr("style");
    });
});

function update_details_visibility() {
    var window_width = $(window).width();

    if (details_shown === null) {
        if (window_width < 992) {
            collapse_details("hide", false);
        }
        else {
            collapse_details("show", false);
        }
    }

    else if (window_width >= 992) {
        collapse_details("show", false);
    }

    else if (details_shown == false) {
        collapse_details("hide", false);
    }

    else if (details_shown == true) {
        collapse_details("show", false);
    }
}

function collapse_details(visibility, transition) {
    transition = transition !== undefined ? transition : true;
    var details_collapse = $("#content-details-collapse");

    if (transition === true) {
        details_collapse.collapse(visibility);
    }
    else if (transition === false) {
        details_collapse.css("transition", "none");
        details_collapse.collapse(visibility);
    }

    var window_width = $(window).width();

    if (window_width >= 992) {
        $(".content-details-hide, .content-details-show").hide();
    }
    else if (visibility == "show") {
        $(".content-details-hide").show();
        $(".content-details-show").hide();
    }
    else if (visibility == "hide") {
        $(".content-details-hide").hide();
        $(".content-details-show").show();
    }
}
