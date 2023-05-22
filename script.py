import importlib
import logging
import types
import typing

import gradio as gr
import oobabot

import modules

from . import oobabot_constants, oobabot_layout, oobabot_worker

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: automatically use loaded persona
# todo: get Oobabooga settings dir?

params = {
    "is_tab": True,
    "activate": True,
    "config_file": "oobabot-config.yml",
}

##################################
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

##################################

oobabot_worker = oobabot_worker.OobabotWorker(
    modules.shared.args.api_streaming_port,
    params["config_file"],
)
oobabot_layout = oobabot_layout.OobabotLayout()

##################################
# discord token UI

TOKEN_LEN_CHARS = 72


def token_is_plausible(token: str) -> bool:
    return len(token.strip()) >= TOKEN_LEN_CHARS


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
        token = token.strip()
        is_token_valid = oobabot_worker.bot.test_discord_token(token)
        if is_token_valid:
            oobabot_worker.bot.settings.discord_settings.set("discord_token", token)
            oobabot_worker.bot.settings.write_to_file(params["config_file"])
            oobabot_worker.reload()

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


def do_get_chars():
    return oobabot_layout.character_dropdown.update(
        choices=modules.utils.get_available_characters(),
        interactive=True,
        # value=characters[0],???
    )


def connect_character_actions() -> None:
    oobabot_layout.character_dropdown.attach_load_event(
        do_get_chars,
        None,
    )
    oobabot_layout.reload_character_button.click(
        do_get_chars,
        inputs=[],
        outputs=[oobabot_layout.character_dropdown],
    )


##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    token = oobabot_worker.bot.settings.discord_settings.get_str("discord_token")
    plausible_token = token_is_plausible(token)

    oobabot_layout.setup_ui(
        get_logs=oobabot_worker.get_logs,
        has_plausible_token=plausible_token,
    )

    connect_token_actions()
    connect_character_actions()
    # todo: connect other actions

    set_values_from_token(token, plausible_token)
    set_values_from_settings(oobabot_worker.bot.settings)


def set_values_from_token(token: str, plausible_token: bool) -> None:
    def enable_when_token_plausible(component: gr.components.IOComponent) -> None:
        component.attach_load_event(
            lambda: component.update(interactive=plausible_token),
            None,
        )

    # set token widget value, it will cascade interactive-enabling events
    # to other UI components
    oobabot_layout.discord_token_textbox.attach_load_event(
        lambda: oobabot_layout.discord_token_textbox.update(value=token),
        None,
    )
    enable_when_token_plausible(oobabot_layout.discord_token_save_button)
    oobabot_layout.discord_invite_link_html.attach_load_event(
        lambda: oobabot_layout.discord_invite_link_html.update(
            # pretend that the token is valid here if it's plausible
            value=update_discord_invite_link(
                token,
                token_is_plausible,
                False,
            )
        ),
        None,
    )
    enable_when_token_plausible(oobabot_layout.ive_done_all_this_button)
    enable_when_token_plausible(oobabot_layout.start_button)


def set_values_from_settings(settings: oobabot.settings.Settings):
    oobabot_layout.ai_name_textbox.attach_load_event(
        lambda: oobabot_layout.ai_name_textbox.update(
            value=settings.persona_settings.get_str("ai_name")
        ),
        None,
    )
    oobabot_layout.persona_textbox.attach_load_event(
        lambda: oobabot_layout.persona_textbox.update(
            value=settings.persona_settings.get_str("persona")
        ),
        None,
    )
    # todo: wake words
    # wake_words_textbox: gr.Textbox

    # discord behavior widgets
    split_responses_radio_group: gr.Radio
    history_lines_slider: gr.Slider
    discord_behavior_checkbox_group: gr.CheckboxGroup


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
