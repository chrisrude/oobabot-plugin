# -*- coding: utf-8 -*-
"""
This manages the oobabot worker thread, as well
as creating the bot itself.
"""
import os
import threading
import typing

import gradio as gr
from oobabot import oobabot

from oobabot_plugin import input_handlers
from oobabot_plugin import layout


class OobabotWorker:
    """
    This class is responsible for running oobabot in a worker thread.
    It also connects the plugin's input fields to the oobabot's internal
    settings representation.
    """

    bot: oobabot.Oobabot
    handlers: typing.Dict[
        gr.components.IOComponent,
        input_handlers.ComponentToSetting,
    ]

    def __init__(
        self,
        port: int,
        config_file: str,
        layout: layout.OobabotLayout,
    ):
        """
        port: The port the streaming API is running on
        """
        self.config_file = config_file
        self.port = port
        self.thread = None
        self.stopping = False
        self.layout = layout
        self.reload()

    def reload(self) -> None:
        """
        Stops oobabot if it's running, then reloads it.
        """
        if self.thread is not None:
            self.stopping = True
            self.bot.stop()
            self.thread.join()
            self.stopping = False
            self.thread = None

        args = [
            "--config",
            os.path.abspath(self.config_file),
            "--base-url",
            f"ws://localhost:{self.port}/",
        ]
        self.bot = oobabot.Oobabot(args)
        self.handlers = {}

    def start(self) -> None:
        """
        Stops the oobabot if it's running, then starts it.
        """
        self.reload()
        self.thread = threading.Thread(target=self.bot.start)
        self.thread.start()

    def is_running(self) -> bool:
        """
        Returns True if oobabot is running.
        This does not mean that it is connected to discord,
        only that its main loop is running.
        """
        return self.thread is not None and self.thread.is_alive()

    def has_discord_token(self) -> bool:
        """
        Returns True if the user has entered a discord token.
        """
        if self.bot.settings.discord_settings.get_str("discord_token"):
            return True
        return False

    def get_logs(self) -> str:
        """
        Returns the logs from the oobabot.
        """
        if self.bot is None:
            return ""

        lines = oobabot.fancy_logger.recent_logs.get_all()
        return (
            '<div class="oobabot-log">' + "\n<br>".join(lines) + "</div></body></html>"
        )

    def save_settings(self):
        self.bot.settings.write_to_file(self.config_file)

    def get_input_handlers(
        self,
        fn_get_character_list: typing.Callable[[], typing.List[str]],
    ) -> typing.Dict[gr.components.IOComponent, input_handlers.ComponentToSetting]:
        if self.handlers:
            return self.handlers

        layout = self.layout
        settings = self.bot.settings

        components_to_settings = [
            input_handlers.SimpleComponentToSetting(
                layout.discord_token_textbox,
                settings.discord_settings,
                "discord_token",
            ),
            input_handlers.CharacterComponentToSetting(
                layout.character_dropdown,
                settings.persona_settings,
                "persona_file",
                fn_get_character_list,
            ),
            input_handlers.SimpleComponentToSetting(
                layout.ai_name_textbox,
                settings.persona_settings,
                "ai_name",
            ),
            input_handlers.SimpleComponentToSetting(
                layout.persona_textbox,
                settings.persona_settings,
                "persona",
            ),
            input_handlers.ListComponentToSetting(
                layout.wake_words_textbox,
                settings.persona_settings,
                "wakewords",
            ),
            input_handlers.ResponseRadioComponentToSetting(
                layout.split_responses_radio_group,
                settings.discord_settings,
                layout.SINGLE_MESSAGE,
                layout.STREAMING,
                layout.BY_SENTENCE,
            ),
            input_handlers.SimpleComponentToSetting(
                layout.history_lines_slider,
                settings.discord_settings,
                "history_lines",
            ),
            input_handlers.CheckboxGroupToSetting(
                layout.discord_behavior_checkbox_group,
                settings.discord_settings,
                [
                    ("ignore_dms", layout.IGNORE_DMS),
                    ("reply_in_thread", layout.REPLY_IN_THREAD),
                ],
            ),
            input_handlers.SimpleComponentToSetting(
                layout.stable_diffusion_url_textbox,
                settings.stable_diffusion_settings,
                "stable_diffusion_url",
            ),
            input_handlers.SimpleComponentToSetting(
                layout.stable_diffusion_prefix,
                settings.stable_diffusion_settings,
                "extra_prompt_text",
            ),
        ]

        # make a map from component to setting
        self.handlers = {c.component: c for c in components_to_settings}
        return self.handlers
