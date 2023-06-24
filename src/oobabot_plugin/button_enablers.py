# -*- coding: utf-8 -*-
"""
Enables or disables buttons based on the state of other inputs.
"""
import gradio as gr

from oobabot_plugin import layout as oobabot_layout
from oobabot_plugin import strings
from oobabot_plugin import worker as oobabot_worker


def init_enablers(
    layout: oobabot_layout.OobabotLayout,
    token: str,
    worker: oobabot_worker.OobabotWorker,
    plausible_token: bool,
) -> None:
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

    enable_when_token_plausible(layout.discord_token_save_button)
    enable_when_token_plausible(layout.ive_done_all_this_button)
    enable_when_token_plausible(layout.start_button)

    # initialize the discord invite link value
    layout.discord_invite_link_html.attach_load_event(
        lambda: layout.discord_invite_link_html.update(
            # pretend that the token is valid here if it's plausible,
            # but don't show a green check
            value=strings.update_discord_invite_link(
                token,
                plausible_token,
                False,
                worker.bot.generate_invite_url,
            )
        ),
        None,
    )

    layout.start_button.attach_load_event(
        lambda: layout.start_button.update(interactive=not worker.is_running()),
        every=1.0,
    )

    layout.stop_button.attach_load_event(
        lambda: layout.stop_button.update(interactive=worker.is_running()),
        every=1.0,
    )

    # turn on a handler for the token textbox which will enable
    # the save button only when the entered token looks plausible
    layout.discord_token_textbox.change(
        lambda token: layout.discord_token_save_button.update(
            interactive=strings.token_is_plausible(token)
        ),
        inputs=[layout.discord_token_textbox],
        outputs=[
            layout.discord_token_save_button,
        ],
    )
