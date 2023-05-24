# -*- coding: utf-8 -*-
"""
Main entry point for the oobabot plugin.
This file's name is mandatory, and must be "script.py",
as that's how the plugin loader finds it.
"""
from oobabot_plugin import bootstrap

SCRIPT_PY_VERSION = "0.1.8"


params = {
    # can be changed in settings.json with:
    #   "oobabot-config_file string": "~/oobabot/config.yml",
    "config_file": "",
    "display_name": "oobabot",
    "is_tab": True,
}


# pylint: disable=C0103
# pylint doesn't like the method name, but it's
# mandated by the extension interface
def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    bootstrap.plugin_ui(
        script_py_version=SCRIPT_PY_VERSION,
        params=params,
    )


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return bootstrap.custom_css(
        script_py_version=SCRIPT_PY_VERSION,
        params=params,
    )


def custom_js() -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    return bootstrap.custom_js(
        script_py_version=SCRIPT_PY_VERSION,
        params=params,
    )
