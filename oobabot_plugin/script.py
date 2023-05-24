# -*- coding: utf-8 -*-
"""
Main entry point for the oobabot plugin.
This file's name is mandatory, and must be "script.py",
as that's how the plugin loader finds it.
"""
from oobabot_plugin import controller
from oobabot_plugin import strings

# we'll try to discover what the user has actually set the
# port to, but if we fail for some reason, fall back to this
DEFAULT_STREAMING_API_PORT = 5005

# standard config file name, can be overridden in settings.json
DEFAULT_CONFIG_FILE = "oobabot-config.yml"


params = {
    # can be changed in settings.json with:
    #   "oobabot-config_file string": "~/oobabot/config.yml",
    "config_file": DEFAULT_CONFIG_FILE,
    "display_name": "oobabot",
    "is_tab": True,
}


# allow our logging to use the original version of StreamHandler.emit,
# then reapply the monkey-patch so it doesn't affect anyone else
oobabot_logger = strings.repair_logging()


# pylint: disable=C0103
# pylint doesn't like the method name, but it's
# mandated by the extension interface
def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """

    # use optimistic defaults, in case the probing process
    # fails for some reason.  If either of these fail, the
    # worst that will happen is that the user will see an error
    # message when they start the bot, so they have some
    # chance of fixing it from there.

    streaming_port = DEFAULT_STREAMING_API_PORT
    api_extension_loaded = True
    try:
        # pylint: disable=import-outside-toplevel
        from modules import shared

        # pylint: enable=import-outside-toplevel

        if shared.args:
            if shared.args.extensions:
                if "api" not in shared.args.extensions:
                    api_extension_loaded = False
            if shared.args.api_streaming_port:
                streaming_port = shared.args.api_streaming_port

    except ImportError as e:
        if oobabot_logger:
            oobabot_logger.warning(
                "oobabot: could not load shared module, using defaults: %s", e
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


# pylint: enable=C0103


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return strings.get_css()


def custom_js() -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    return strings.get_js()
