# -*- coding: utf-8 -*-
"""
Enables or disables buttons based on the state of other inputs.
"""
import gradio as gr

from oobabot_plugin import layout as oobabot_layout
from oobabot_plugin import strings
from oobabot_plugin import worker as oobabot_worker


class ButtonEnablers:
    """
    Enables or disables buttons based on the running state of the bot.
    """

    def __init__(
        self,
        layout: oobabot_layout.OobabotLayout,
        token: str,
        worker: oobabot_worker.OobabotWorker,
        plausible_token: bool,
    ) -> None:
        """
        Sets up handlers which will enable or disable buttons
        based on the state of other inputs.
        """
        self.is_token_plausible = plausible_token
        self.layout = layout
        self.worker = worker

        # first, set up the initial state of the buttons, when the UI first loads
        def enable_when_token_plausible(component: gr.components.IOComponent) -> None:
            component.attach_load_event(
                lambda: component.update(interactive=self.is_token_plausible),
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
                    self.is_token_plausible,
                    False,
                    worker.bot.generate_invite_url,
                )
            ),
            None,
        )

        def on_token_change(token: str):
            self.is_token_plausible = strings.token_is_plausible(token)
            return (
                layout.discord_token_save_button.update(
                    interactive=self.is_token_plausible
                ),
                self.running_state_update(),
            )

        # the running state can change when the token changes, or
        # when the bot starts or stops
        layout.discord_token_textbox.change(
            on_token_change,
            inputs=[layout.discord_token_textbox],
            outputs=[
                layout.discord_token_save_button,
                layout.running_state_textbox,
            ],
        )

        # monitor the running state all the time, to monitor
        # for two cases:
        #   1. the bot was already running when the user loaded the page
        #   2. the bot stopped on its own, perhaps due to an error
        layout.running_state_textbox.attach_load_event(
            self.running_state_update,
            every=strings.QUICK_UPDATE_INTERVAL_SECONDS,
        )

        # enable or disable all other input controls based on the running state
        layout.running_state_textbox.change(
            self._handle_running_state_change,
            inputs=[layout.running_state_textbox],
            outputs=[
                layout.status_html,
                layout.start_button,
                layout.stop_button,
                layout.save_settings_button,
                layout.discord_token_save_button,
                layout.advanced_save_settings_button,
                layout.advanced_yaml_editor,
                *self._get_input_handlers().keys(),
            ],
        )

    # a hidden textbox which reflects the running state
    # of the bot.  This can be one of these values:
    #  - "" (empty string) - unknown state (during startup)
    #  - "no_token" - there is no token set
    #  - "running" - bot is running
    #  - "stopped" - bot is stopped
    def _current_running_state(self, is_running=None) -> str:
        if is_running is None:
            is_running = self.worker.is_running()
        if not self.is_token_plausible:
            return "no_token"
        if is_running:
            return "running"
        return "stopped"

    def running_state_update(self, is_running=None):
        return self.layout.running_state_textbox.update(
            value=self._current_running_state(is_running)
        )

    # lots to do here:
    #  if the bot is running, disable all inputs
    #  if the bot is stopped, but has a valid token, enable all inputs
    #  if the bot is stopped and does not have a valid token, disable
    #  all inputs except for the advanced settings editor
    def _handle_running_state_change(self, running_state: str):
        if running_state == "running":
            enable_stop = True
            enable_advanced = False
            enable_inputs_and_start = False
        elif running_state in ("no_token", ""):
            enable_stop = False
            enable_advanced = True
            enable_inputs_and_start = False
        elif running_state == "stopped":
            enable_stop = False
            enable_advanced = True
            enable_inputs_and_start = True
        else:
            raise ValueError(f"unknown running state: {running_state}")

        # order of outputs:
        #   layout.status_markdown,
        #   layout.start_button,
        #   layout.stop_button,
        #   layout.save_settings_button,
        #   layout.discord_token_save_button
        #   layout.advanced_save_settings_button,
        #   layout.advanced_yaml_editor,
        #   *self._get_input_handlers().keys(),
        results = [
            self.layout.status_html.update(
                value=strings.status_heading(running_state),
            ),
            self.layout.start_button.update(interactive=enable_inputs_and_start),
            self.layout.stop_button.update(interactive=enable_stop),
            self.layout.save_settings_button.update(
                interactive=enable_inputs_and_start
            ),
            self.layout.discord_token_save_button.update(
                interactive=enable_inputs_and_start
            ),
            self.layout.advanced_save_settings_button.update(
                interactive=enable_advanced
            ),
            self.layout.advanced_yaml_editor.update(interactive=enable_advanced),
        ]
        for handler in self._get_input_handlers().values():
            enable = enable_inputs_and_start
            if handler.component == self.layout.discord_token_textbox:
                # when we're missing a token, be sure to leave the
                # token textbox enabled!
                enable = enable_advanced
            if enable:
                results.append(handler.enabled())
            else:
                results.append(handler.disabled())
        return tuple(results)

    def _enable_disable_inputs(self, is_running: bool):
        """
        Enables or disables all the inputs on the page
        based on whether the bot is running or not.

        Maintenance note: this logic is also shadowed in
        the _init_input_enablers() method, so if you update
        this, update that too.
        """
        results = []
        for handler in self._get_input_handlers().values():
            if is_running:
                results.append(handler.disabled())
            else:
                results.append(handler.enabled())

        results.append(self.layout.start_button.update(interactive=not is_running))
        results.append(self.layout.stop_button.update(interactive=is_running))
        results.append(
            self.layout.advanced_save_settings_button.update(interactive=not is_running)
        )
        results.append(
            self.layout.advanced_yaml_editor.update(interactive=not is_running)
        )
        return results

    # todo: put this in a better spot?
    def _get_input_handlers(self):
        return self.worker.get_input_handlers(strings.get_available_characters)
