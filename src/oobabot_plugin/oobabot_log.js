var keep_at_bottom = false;

window.onscroll = function (_evt) {
    keep_at_bottom = ((window.innerHeight + window.scrollY + 150) >= document.body.offsetHeight);
};

function is_visible(id) {
    var el = document.getElementById(id);
    return (el !== null) && (el.offsetParent !== null);
}

var intervalId = setInterval(function () {
    var selected = is_visible('oobabot-tab-audio');
    if (keep_at_bottom && selected) {
        window.scrollTo(0, document.body.scrollHeight);
    }
}, 500);
