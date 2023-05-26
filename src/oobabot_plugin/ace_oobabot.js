function onIsThere(fn, element_id) {
    // see if the element is there yet
    var element = document.getElementById(element_id);
    if (element) {
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
    if (document.body.classList.contains('dark')) {
        editor.setTheme("ace/theme/github_dark");
    } else {
        editor.setTheme("ace/theme/github");
    }
    editor.session.setTabSize(4);
    editor.session.setUseSoftTabs(true);

    var save_button = document.getElementById('oobabot-advanced-save-settings');
    if (save_button == undefined || save_button.disabled) {
        editor.setReadOnly(true);
    }

    editor.session.setMode("ace/mode/yaml");
    window.ooba_editor = editor;
    document.getElementById('editor').style.display = 'block';
}

function ooba_extract(x) {
    // if window.ooba_editor is undefined, then we're not in the right place
    if (window.ooba_editor == undefined) {
        return x;
    }
    return window.ooba_editor.getValue();
}

function ace_oobabot_init(...args) {
    // todo: better?
    onIsThere(ace_oobabot, 'editor');
    return args;
}
window.ace_oobabot_init = ace_oobabot_init;
window.ooba_extract = ooba_extract;
