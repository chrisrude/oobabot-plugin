import enum
import importlib
import logging
import types
import typing

import modules

import oobabot

from . import oobabot_constants, oobabot_layout, oobabot_worker

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: automatically use loaded persona
# todo: get Oobabooga settings dir
# todo: a way to clear the discord token

params = {
    "is_tab": True,
    "activate": True,
    "config_file": "config.yml",
}


# so, logging_colors.py, rather than using the logging module's built-in
# formatter, is monkey-patching the logging module's StreamHandler.emit.
# This is a problem for us, because we also use the logging module, but
# don't want ANSI color codes showing up in HTML.  We also don't want
# to break their logging.
#
# So, we're going to save their monkey-patched emit, reload the logging
# module, save off the "real" emit, then re-apply their monkey-patch.
#
# We need to do all this before we create the oobabot_worker, so that
# the logs created during startup are properly formatted.

# save the monkey-patched emit
hacked_emit = logging.StreamHandler.emit

# reload the logging module
importlib.reload(logging)

# create our logger early
oobabot.fancy_logger.init_logging(logging.DEBUG, True)
ooba_logger = oobabot.fancy_logger.get()

# manually apply the "correct" emit to each of the StreamHandlers
# that fancy_logger created
for handler in ooba_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.emit = types.MethodType(logging.StreamHandler.emit, handler)

logging.StreamHandler.emit = hacked_emit


class OobabotUIState(enum.Enum):
    CLEAN = 0  # user has no discord token
    HAS_TOKEN = 1  # user has discord token, but no bot persona
    STOPPED = 2  # user has discord token and bot persona, but bot is stopped
    STARTED = 3  # user has discord token and bot persona, and bot is started
    STOPPING = 4  # user has discord token and bot persona, and bot is stopping


oobabot_worker = oobabot_worker.OobabotWorker(
    modules.shared.args.api_streaming_port,
    params["config_file"],
)

oobabot_layout = oobabot_layout.OobabotLayout()

state = OobabotUIState.CLEAN


##################################
# behavior


def determine_current_state() -> OobabotUIState:
    if not oobabot_worker.has_discord_token():
        return OobabotUIState.CLEAN
    if oobabot_worker.is_running():
        return OobabotUIState.STARTED
    if oobabot_worker.stopping:
        return OobabotUIState.STOPPING
    return OobabotUIState.STOPPED


# def enable_appropriate_widgets(state: OobabotUIState) -> None:
#     # start by disabling all the things
#     oobabot_layout.disable_all()

#     match state:
#         case OobabotUIState.CLEAN:
#             oobabot_layout.welcome_accordion.open = True
#             oobabot_layout.discord_token_textbox.interactive = True
#             oobabot_layout.discord_token_save_button.interactive = True

#         case OobabotUIState.HAS_TOKEN:
#             print("HAS_TOKEN")
#             oobabot_layout.welcome_accordion.open = True
#             oobabot_layout.discord_token_textbox.interactive = True
#             oobabot_layout.discord_token_save_button.interactive = True
#             oobabot_layout.discord_invite_link_markdown.interactive = True
#             # todo: set link value
#             oobabot_layout.ive_done_all_this_button.interactive = True
#             oobabot_layout.set_all_setting_widgets_interactive(True)

#         case OobabotUIState.STOPPED:
#             print("STOPPED")
#             oobabot_layout.welcome_accordion.open = False
#             oobabot_layout.discord_token_save_button.interactive = True
#             oobabot_layout.ive_done_all_this_button.interactive = True
#             oobabot_layout.start_button.interactive = True
#             oobabot_layout.set_all_setting_widgets_interactive(True)

#         case OobabotUIState.STARTED:
#             print("STARTED")
#             oobabot_layout.welcome_accordion.open = False
#             oobabot_layout.discord_token_save_button.interactive = True
#             oobabot_layout.ive_done_all_this_button.interactive = True
#             oobabot_layout.stop_button.interactive = True
#             oobabot_layout.set_all_setting_widgets_interactive(False)

#         case OobabotUIState.STOPPING:
#             print("STOPPING")
#             oobabot_layout.welcome_accordion.open = False
#             oobabot_layout.discord_token_save_button.interactive = True
#             oobabot_layout.ive_done_all_this_button.interactive = True
#             oobabot_layout.set_all_setting_widgets_interactive(True)

##################################
# discord token UI

TOKEN_LEN_CHARS = 72


def token_is_plausible(token: str) -> bool:
    return len(token) >= TOKEN_LEN_CHARS


def make_link_from_token(
    token: str, fn_calc_invite_url: typing.Optional[callable]
) -> str:
    if not token or not fn_calc_invite_url:
        return "A link will appear here once you have set your Discord token."
    link = fn_calc_invite_url(token)
    return (
        f'<a href="{link}" id="oobabot-invite-link" target="_blank">Click here to <pre>'
        + "invite your bot</pre> to a Discord server</a>."
    )


def update_discord_invite_link(new_token: str, is_token_valid: bool, is_tested: bool):
    new_token = new_token.strip()
    prefix = ""
    if is_tested:
        if is_token_valid:
            prefix = "✅ Your token is valid.<br><br>"
        else:
            prefix = "❌ Your token is invalid."
    if is_token_valid:
        return prefix + make_link_from_token(
            new_token, oobabot_worker.bot.generate_invite_url
        )
    if new_token:
        return prefix
    return "A link will appear here once you have set your Discord token."


def connect_token_actions() -> None:
    # TODO: toggled open and closed
    # oobabot_layout.welcome_accordion,

    # turn on save button when token is entered and
    # looks plausible
    oobabot_layout.discord_token_textbox.change(
        lambda token: oobabot_layout.discord_token_save_button.update(
            interactive=token_is_plausible(token)
        ),
        inputs=[oobabot_layout.discord_token_textbox],
        outputs=[
            oobabot_layout.discord_token_save_button,
        ],
    )

    def handle_save_click(token: str):
        is_token_valid = oobabot_worker.bot.test_discord_token(token.strip())
        return (
            oobabot_layout.discord_invite_link_html.update(
                value=update_discord_invite_link(token, is_token_valid, True)
            ),
            oobabot_layout.ive_done_all_this_button.update(interactive=is_token_valid),
        )

    oobabot_layout.discord_token_save_button.click(
        handle_save_click,
        inputs=[oobabot_layout.discord_token_textbox],
        outputs=[
            oobabot_layout.discord_invite_link_html,
            oobabot_layout.ive_done_all_this_button,
        ],
    )


##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """

    oobabot_layout.setup_ui(
        get_logs=oobabot_worker.get_logs,
    )

    # current_state = determine_current_state()
    # enable_appropriate_widgets(current_state)

    connect_token_actions()
    # todo: connect other actions

    # set token widget, it should cascade to other widgets
    token = oobabot_worker.bot.settings.discord_settings.get_str("discord_token")
    oobabot_layout.discord_token_textbox.attach_load_event(
        lambda: oobabot_layout.discord_token_textbox.update(value=token),
        None,
    )
    oobabot_layout.discord_token_save_button.attach_load_event(
        lambda: oobabot_layout.discord_token_save_button.update(
            interactive=token_is_plausible(token)
        ),
        None,
    )
    oobabot_layout.discord_invite_link_html.attach_load_event(
        lambda: oobabot_layout.discord_invite_link_html.update(
            # pretend that the token is valid here if it's plausible
            value=update_discord_invite_link(
                token,
                token_is_plausible(token),
                False,
            )
        ),
        None,
    )
    oobabot_layout.ive_done_all_this_button.attach_load_event(
        lambda: oobabot_layout.ive_done_all_this_button.update(
            interactive=token_is_plausible(token)
        ),
        None,
    )


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return oobabot_constants.LOG_CSS

    # CLEAN = 0  # user has no discord token
    # HAS_TOKEN = 1  # user has discord token, but no bot persona
    # STOPPED = 2  # user has discord token and bot persona, but bot is stopped
    # STARTED = 3  # user has discord token and bot persona, and bot is started
    # STOPPING = 4  # user has discord token and bot persona, and bot is stopping


def custom_js() -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    return oobabot_constants.CUSTOM_JS
