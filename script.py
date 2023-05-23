import importlib
import logging
import types
import typing

import gradio as gr
import modules

import oobabot

from . import oobabot_constants, oobabot_input_handlers, oobabot_layout, oobabot_worker

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: show that we're actually using the selected character
# add stable diffusion settings
# todo: wait for the bot to stop gracefully

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
            prefix = "✔️ Your token is valid.<br><br>"
        else:
            prefix = "❌ Your token is invalid."
    if is_token_valid:
        return prefix + make_link_from_token(
            new_token, oobabot_worker.bot.generate_invite_url
        )
    if new_token:
        return prefix
    return "A link will appear here once you have set your Discord token."


def init_button_enablers(token: str, plausible_token: bool) -> None:
    """
    Sets up handlers which will enable or disable buttons
    based on the state of other inputs.
    """

    # first, set up the initial state of the buttons, when the UI first loads
    def enable_when_token_plausible(component: gr.components.IOComponent) -> None:
        component.attach_load_event(
            lambda: component.update(interactive=plausible_token),
            None,
        )

    enable_when_token_plausible(oobabot_layout.discord_token_save_button)
    enable_when_token_plausible(oobabot_layout.ive_done_all_this_button)
    enable_when_token_plausible(oobabot_layout.start_button)

    # initialize the discord invite link value
    oobabot_layout.discord_invite_link_html.attach_load_event(
        lambda: oobabot_layout.discord_invite_link_html.update(
            # pretend that the token is valid here if it's plausible,
            # but don't show a green check
            value=update_discord_invite_link(
                token,
                token_is_plausible,
                False,
            )
        ),
        None,
    )

    # turn on a handler for the token textbox which will enable
    # the save button only when the entered token looks plausible
    oobabot_layout.discord_token_textbox.change(
        lambda token: oobabot_layout.discord_token_save_button.update(
            interactive=token_is_plausible(token)
        ),
        inputs=[oobabot_layout.discord_token_textbox],
        outputs=[
            oobabot_layout.discord_token_save_button,
        ],
    )


input_handlers: dict[
    gr.components.IOComponent, oobabot_input_handlers.ComponentToSetting
]


def init_input_handlers() -> None:
    global input_handlers
    input_handlers = oobabot_input_handlers.get_all(
        oobabot_layout,
        oobabot_worker.bot.settings,
    )


def get_input_handlers() -> dict:
    global input_handlers
    return input_handlers


def init_button_handlers() -> None:
    """
    Sets handlers that are called when buttons are pressed
    """

    def handle_save_click(*args):
        # we've been passed the value of every input component,
        # so pass each in turn to our input handler

        results = []

        # iterate over args and input_handlers in parallel
        for new_value, handler in zip(args, get_input_handlers().values()):
            update = handler.update_component_from_event(new_value)
            results.append(update)

        oobabot_worker.bot.settings.write_to_file(params["config_file"])
        init_input_handlers()

        return tuple(results)

    def handle_save_discord_token(*args):
        # we've been passed the value of every input component,
        # so pass each in turn to our input handler

        # result is a tuple, convert it to a list so we can modify it
        results = list(handle_save_click(*args))

        # get the token from the settings
        token = oobabot_worker.bot.settings.discord_settings.get_str("discord_token")
        is_token_valid = oobabot_worker.bot.test_discord_token(token)

        # results has most of our updates, but we also need to provide ones
        # for the discord invite link and the "I've done all this" button
        results.append(
            oobabot_layout.discord_invite_link_html.update(
                value=update_discord_invite_link(token, is_token_valid, True)
            )
        )
        results.append(
            oobabot_layout.ive_done_all_this_button.update(interactive=is_token_valid)
        )
        results.append(oobabot_layout.start_button.update(interactive=is_token_valid))

        return tuple(results)

    oobabot_layout.discord_token_save_button.click(
        handle_save_discord_token,
        inputs=[*get_input_handlers().keys()],
        outputs=[
            *get_input_handlers().keys(),
            oobabot_layout.discord_invite_link_html,
            oobabot_layout.ive_done_all_this_button,
            oobabot_layout.start_button,
        ],
    )

    def update_available_characters():
        choices = modules.utils.get_available_characters()
        oobabot_layout.character_dropdown.update(
            choices=choices,
            interactive=True,
        )

    oobabot_layout.reload_character_button.click(
        update_available_characters,
        inputs=[],
        outputs=[oobabot_layout.character_dropdown],
    )

    oobabot_layout.save_settings_button.click(
        handle_save_click,
        inputs=[*get_input_handlers().keys()],
        outputs=[*get_input_handlers().keys()],
    )

    def handle_start(*args):
        # things to do!
        # 1. save settings
        # 2. disable all the inputs
        # 3. disable the start button
        # 4. enable the stop button
        # 5. start the bot
        results = list(handle_save_click(*args))
        # the previous handler will have updated the input's values, but we also
        # want to disable them.  We can do this by merging the dicts.
        for update_dict, handler in zip(results, get_input_handlers().values()):
            update_dict.update(handler.disabled())

        # we also need to disable the start button, and enable the stop button
        results.append(oobabot_layout.start_button.update(interactive=False))
        results.append(oobabot_layout.stop_button.update(interactive=True))

        # now start the bot!
        oobabot_worker.start()

        return list(results)

    # start button!!!!
    oobabot_layout.start_button.click(
        handle_start,
        inputs=[
            *get_input_handlers().keys(),
            oobabot_layout.start_button,
            oobabot_layout.stop_button,
        ],
        outputs=[
            *get_input_handlers().keys(),
            oobabot_layout.start_button,
            oobabot_layout.stop_button,
        ],
    )

    def handle_stop(*args):
        # things to do!
        # 1. stop the bot
        # 2. enable all the inputs
        # 3. enable the start button
        # 4. disable the stop button
        oobabot_worker.reload()
        init_input_handlers()

        results = []
        for handler in get_input_handlers().values():
            results.append(handler.enabled())

        results.append(oobabot_layout.start_button.update(interactive=True))
        results.append(oobabot_layout.stop_button.update(interactive=False))

        return tuple(results)

    # stop button!!!!
    oobabot_layout.stop_button.click(
        handle_stop,
        inputs=[
            *get_input_handlers().keys(),
            oobabot_layout.start_button,
            oobabot_layout.stop_button,
        ],
        outputs=[
            *get_input_handlers().keys(),
            oobabot_layout.start_button,
            oobabot_layout.stop_button,
        ],
    )


##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    token = oobabot_worker.bot.settings.discord_settings.get_str("discord_token")
    plausible_token = token_is_plausible(token)
    stable_diffusion_keywords = (
        oobabot_worker.bot.settings.stable_diffusion_settings.get("image_words")
    )

    oobabot_layout.layout_ui(
        get_logs=oobabot_worker.get_logs,
        has_plausible_token=plausible_token,
        stable_diffusion_keywords=stable_diffusion_keywords,
    )

    # create our own handlers for every input event which will map
    # between our settings object and its corresponding UI component
    init_input_handlers()

    # for all input components, add initialization handlers to
    # set their values from what we read from the settings file
    for component_to_setting in get_input_handlers().values():
        component_to_setting.init_component_from_setting()

    # sets up what happens when each button is pressed
    init_button_handlers()

    # enables or disables buttons based on the state of other inputs
    init_button_enablers(token, plausible_token)


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return oobabot_constants.LOG_CSS


def custom_js() -> str:
    """
    Returns custom JavaScript to be injected into the UI.
    """
    return oobabot_constants.CUSTOM_JS
