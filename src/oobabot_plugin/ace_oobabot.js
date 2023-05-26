function onIsThere(fn, element_id) {
    // see if the element is there yet
    var element = document.getElementById(element_id);
    if (element) {
        console.log("found " + element_id);
        fn();
    } else {
        // if not, wait a bit and try again
        setTimeout(function () {
            onIsThere(fn, element_id);
        }, 100);
    }
}

// needs to accept n arguments, return n+1 arguments
function ace_oobabot() {
    var editor = ace.edit("editor", {
        autoScrollEditorIntoView: true,
        cursorStyle: "ace",
        maxLines: 1000,
        showPrintMargin: false,
        useWorker: false,
    });
    editor.setTheme("ace/theme/twilight");
    editor.session.setTabSize(4);
    editor.session.setUseSoftTabs(true);

    editor.session.setMode("ace/mode/yaml");
    document.getElementById('editor').style.display = 'block';
}

function ace_oobabot_init(...args) {
    // todo: better?
    onIsThere(ace_oobabot, 'editor');
    return args;
}
window.ace_oobabot_init = ace_oobabot_init;
