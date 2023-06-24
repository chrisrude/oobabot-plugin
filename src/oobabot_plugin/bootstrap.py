# -*- coding: utf-8 -*-
"""
Will run in the context of the oobabooga server.  Called directly from
script.py.  Responsibilities include:
 - gathering any necessary data from the oobabooga process itself
 - installing a new version of script.py if necessary
 - creating and launching our actual plugin
"""

import sys
import threading
import time
import typing

import oobabot

import oobabot_plugin
from oobabot_plugin import controller
from oobabot_plugin import strings

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
        if "standalone" in script_py_version:
            oobabot_logger.debug("oobabot_plugin: running standalone")
        else:
            oobabot_logger.debug(
                "oobabot_plugin: inside Oobabooga, " + "using script.py version: %s",
                SCRIPT_PY_VERSION,
            )
        oobabot_logger.debug("oobabot_plugin version: %s", oobabot_plugin.__version__)
        oobabot_logger.debug("oobabot version: %s", oobabot.__version__)


def plugin_ui(
    script_py_version: str = "",
    params: typing.Optional[dict] = None,
) -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    streaming_port = oobabot_plugin.DEFAULT_STREAMING_API_PORT
    api_extension_loaded = True

    if script_py_version:
        log_script_py_version(script_py_version)

        # use optimistic defaults, in case the probing process
        # fails for some reason.  If either of these fail, the
        # worst that will happen is that the user will see an error
        # message when they start the bot, so they have some
        # chance of fixing it from there.
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

    config_file = DEFAULT_CONFIG_FILE
    if params and params.get("config_file"):
        config_file = params["config_file"]

    # create the controller, which will load our config file.
    # we need to do this before the UI is constructed
    ui_controller = controller.OobabotController(
        streaming_port,
        config_file,
        api_extension_loaded,
    )

    ui_controller.init_ui()

    if script_py_version:
        hack_the_planet()


# pylint: disable=unused-argument
# we want params to be available in the future, as the script.py
# calling us may be from an older version of the plugin than
# this file.  So we'll leave it in the signature, but not use it.
def custom_css(
    script_py_version: str = "",
    params: typing.Optional[dict] = None,
) -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    log_script_py_version(script_py_version)
    return strings.get_css()


def custom_js(
    script_py_version: str = "",
    params: typing.Optional[dict] = None,
) -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    log_script_py_version(script_py_version)
    return strings.get_js()


# pylint: enable=unused-argument


def hack_the_planet():
    threading.Thread(
        target=add_uvicorn_graceful_shutdown_timeout_if_there_isnt_one_already
    ).start()


# pylint: disable=too-many-nested-blocks
# I'm sorry
def add_uvicorn_graceful_shutdown_timeout_if_there_isnt_one_already():
    # this is a hack to work around a bug in gradio.
    # when gradio is using using queued events which run on websockets,
    # when we shut down the server, the client is able to reconnect during
    # the shutdown process, which will cause the server to hang forever.
    # this keeps the "apply and restart the interface" button from working,
    # which is annoying.
    #
    # The reason we run into this is because we're using the "every" update
    # feature, which is using queueing, which seems to be the only use in
    # the main app.
    #
    # A workaround for this is to tell uvicorn (the internal http server
    # for gradio) that it should give up after a certain amount of time.
    # This will cause the server to exit, which will cause the client to
    # make a fresh connection, then everything will work fine, modulo a
    # few error messages in the console about the aborted queuing connections.
    #
    patch_worked = False
    try:
        # pylint: disable=import-outside-toplevel
        # sorry, pylint
        from modules import shared  # type: ignore

        # pylint: enable=import-outside-toplevel
        attempts_remaining = 10

        if shared.gradio:
            if "interface" in shared.gradio:
                if shared.gradio["interface"]:
                    gradio = shared.gradio["interface"]
                    if hasattr(gradio, "is_running"):
                        while not gradio.is_running and attempts_remaining > 0:
                            time.sleep(0.5)
                            attempts_remaining -= 1

                    if hasattr(gradio, "server"):
                        uvicorn_server = gradio.server
                        if hasattr(uvicorn_server, "config"):
                            uvicorn_config = uvicorn_server.config
                            if hasattr(uvicorn_config, "timeout_graceful_shutdown"):
                                if not uvicorn_config.timeout_graceful_shutdown:
                                    uvicorn_config.timeout_graceful_shutdown = 1
                                patch_worked = True

    except ImportError as err:
        if oobabot_logger:
            oobabot_logger.warning(
                "oobabot: could not load shared module, 'apply and restart the "
                + "interface' button may hang.  Please restart the server instead "
                + "of using it: %s",
                err,
            )
    if not patch_worked:
        if oobabot_logger is not None:
            oobabot_logger.warning(
                "oobabot: could not patch uvicorn, so the 'apply and restart "
                + "the interface' button may hang.  Please restart the server "
                + "instead."
            )


# pylint: enable=too-many-nested-blocks
