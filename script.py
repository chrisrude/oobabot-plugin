import enum

import modules

from . import oobabot_constants, oobabot_layout, oobabot_worker

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: automatically use loaded persona
# todo: get oobabooga settings dir

params = {
    "is_tab": True,
    "activate": True,
    "config_file": "oobabot.yml",
}


class OobabotUIState(enum.Enum):
    CLEAN = 0  # user has no discord token
    HAS_TOKEN = 1  # user has discord token, but no bot persona
    STOPPED = 2  # user has discord token and bot persona, but bot is stopped
    STARTED = 3  # user has discord token and bot persona, and bot is started
    STOPPING = 4  # user has discord token and bot persona, and bot is stopping


oobabot_worker_thread = oobabot_worker.OobabotWorker(
    modules.shared.args.api_streaming_port,
    params["config_file"],
)

oobabot_layout = oobabot_layout.OobabotLayout()


##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    oobabot_worker_thread.reload()
    oobabot_layout.setup_ui()


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return oobabot_constants.LOG_CSS

    # stop_button.click(lambda: oobabot_worker_thread.stop(), [], stop_button)
    # start_button.click(lambda: oobabot_worker_thread.start(), [], start_button)
