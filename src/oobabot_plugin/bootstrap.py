# -*- coding: utf-8 -*-
"""
Will run in the context of the oobabooga server.  Called directly from
script.py.  Responsibilities include:
 - gathering any necessary data from the oobabooga process itself
 - installing a new version of script.py if necessary
 - creating and launching our actual plugin
"""

import sys

from oobabot_plugin import controller
from oobabot_plugin import strings

# we'll try to discover what the user has actually set the
# port to, but if we fail for some reason, fall back to this
DEFAULT_STREAMING_API_PORT = 5005

# standard config file name, can be overridden in settings.json
DEFAULT_CONFIG_FILE = "oobabot-config.yml"


# allow our logging to use the original version of StreamHandler.emit,
# then reapply the monkey-patch so it doesn't affect anyone else
oobabot_logger = strings.repair_logging()
SCRIPT_PY_VERSION = None


def log_script_py_version(script_py_version: str):
    if oobabot_logger is None:
        print("oobabot_plugin: could not initialize logging", file=sys.stderr)
        print(
            "oobabot_plugin: script.py version: %d", script_py_version, file=sys.stderr
        )
        return
    # pylint: disable=global-statement
    global SCRIPT_PY_VERSION
    # pylint: enable=global-statement
    if SCRIPT_PY_VERSION is None:
        SCRIPT_PY_VERSION = script_py_version
        oobabot_logger.debug(
            "oobabot_plugin: bootstrapping from script.py version %s", SCRIPT_PY_VERSION
        )


def plugin_ui(script_py_version: str, params: dict) -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    log_script_py_version(script_py_version)

    # use optimistic defaults, in case the probing process
    # fails for some reason.  If either of these fail, the
    # worst that will happen is that the user will see an error
    # message when they start the bot, so they have some
    # chance of fixing it from there.

    streaming_port = DEFAULT_STREAMING_API_PORT
    api_extension_loaded = True
    try:
        # pylint: disable=import-outside-toplevel
        # we need to import this dynamically, because it's
        # not guaranteed to be installed, and will only
        # exist when running in the context of the
        # oobabooga server.
        from modules import shared  # type: ignore

        # pylint: enable=import-outside-toplevel

        if shared.args:
            if shared.args.extensions:
                if "api" not in shared.args.extensions:
                    api_extension_loaded = False
            if shared.args.api_streaming_port:
                streaming_port = shared.args.api_streaming_port

    except ImportError as err:
        if oobabot_logger:
            oobabot_logger.warning(
                "oobabot: could not load shared module, using defaults: %s", err
            )

    config_file = params["config_file"] or DEFAULT_CONFIG_FILE

    # create the controller, which will load our config file.
    # we need to do this before the UI is constructed
    ui_controller = controller.OobabotController(
        streaming_port,
        config_file,
        api_extension_loaded,
    )

    ui_controller.init_ui()


# pylint: disable=unused-argument
# we want params to be available in the future, as the script.py
# calling us may be from an older version of the plugin than
# this file.  So we'll leave it in the signature, but not use it.
def custom_css(script_py_version: str, params: dict) -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    log_script_py_version(script_py_version)
    return strings.get_css()


def custom_js(script_py_version: str, params: dict) -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    log_script_py_version(script_py_version)
    return strings.get_js()


# pylint: enable=unused-argument
