import enum

import modules

from . import oobabot_constants, oobabot_layout, oobabot_worker

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: automatically use loaded persona
# todo: get oobabooga settings dir
# todo: a way to clear the discord token

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

state = OobabotUIState.CLEAN

##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    oobabot_worker_thread.reload()
    oobabot_layout.setup_ui()

    enable_appropriate_widgets(OobabotUIState.STOPPING)


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return oobabot_constants.LOG_CSS


##################################
# behavior
def enable_appropriate_widgets(state: OobabotUIState) -> None:
    # start by disabling all the things
    oobabot_layout.disable_all()

    match state:
        case OobabotUIState.CLEAN:
            oobabot_layout.welcome_accordian.open = True
            oobabot_layout.discord_token_textbox.interactive = True

        case OobabotUIState.HAS_TOKEN:
            oobabot_layout.welcome_accordian.open = True
            oobabot_layout.discord_token_textbox.interactive = True
            oobabot_layout.discord_token_save_button.interactive = True
            oobabot_layout.discord_invite_link_markdown.interactive = True
            # todo: set link value
            oobabot_layout.ive_done_all_this_button.interactive = True
            oobabot_layout.set_all_setting_widgets_interactive(True)

        case OobabotUIState.STOPPED:
            oobabot_layout.welcome_accordian.open = False
            oobabot_layout.discord_token_save_button.interactive = True
            oobabot_layout.ive_done_all_this_button.interactive = True
            oobabot_layout.start_button.interactive = True
            oobabot_layout.set_all_setting_widgets_interactive(True)

        case OobabotUIState.STARTED:
            oobabot_layout.welcome_accordian.open = False
            oobabot_layout.discord_token_save_button.interactive = True
            oobabot_layout.ive_done_all_this_button.interactive = True
            oobabot_layout.stop_button.interactive = True
            oobabot_layout.set_all_setting_widgets_interactive(False)

        case OobabotUIState.STOPPING:
            oobabot_layout.welcome_accordian.open = False
            oobabot_layout.discord_token_save_button.interactive = True
            oobabot_layout.ive_done_all_this_button.interactive = True
            oobabot_layout.set_all_setting_widgets_interactive(True)
