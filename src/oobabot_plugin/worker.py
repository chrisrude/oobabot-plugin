# -*- coding: utf-8 -*-
"""
This manages the oobabot worker thread, as well
as creating the bot itself.
"""
import io
import os
import threading
import typing

import gradio as gr
from oobabot import oobabot

import oobabot_plugin
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
        ]
        if self.port != oobabot_plugin.DEFAULT_STREAMING_API_PORT:
            args.extend(["--base-url", f"ws://localhost:{str(self.port)}"])

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

    def get_log_etag(self) -> int:
        """
        Returns an etag for the oobabot's log.
        """
        if self.bot is None:
            return -1
        return self.bot.log_count()

    def get_logs(self) -> str:
        """
        Returns the logs from the oobabot.
        """
        if self.bot is None:
            return ""

        lines = self.bot.logs()
        return (
            '<div class="oobabot-log">' + "\n<br>".join(lines) + "</div></body></html>"
        )

    def save_settings(self):
        if self.bot is None:
            return
        self.bot.settings.write_to_file(self.config_file)

    def is_voice_enabled(self) -> bool:
        if self.bot is None:
            return False
        return self.bot.is_voice_enabled()

    def get_transcript(self) -> typing.List["oobabot.types.VoiceMessage"]:
        """
        Returns the transcript of the latest voice call from the oobabot,
        or None if there is no transcript.
        """
        if self.bot is None:
            return []
        return self.bot.current_voice_transcript

    def get_fancy_author(
        self, user_id: int
    ) -> typing.Optional["oobabot.types.FancyAuthor"]:
        """
        Returns display information about the given user id,
        or None if the user id could not be found.
        """
        if self.bot is None:
            return None
        return self.bot.fancy_author_info(user_id)

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
            input_handlers.SimpleComponentToSetting(
                layout.plugin_auto_start_checkbox,
                settings.oobabooga_settings,
                "plugin_auto_start",
            ),
        ]

        # make a map from component to setting
        self.handlers = {c.component: c for c in components_to_settings}
        return self.handlers

    def preview_persona(
        self,
        character: str,
        ai_name: str,
        persona: str,
    ) -> typing.Tuple[str, str]:
        """
        Takes the persona settings and returns what the bot will
        end up using, given the settings.

        Returns: (ai_name, persona)
        """
        persona_file = (
            input_handlers.CharacterComponentToSetting.character_name_to_filepath(
                character=character
            )
        )

        persona_handler = oobabot.runtime.persona.Persona(
            {
                "ai_name": ai_name,
                "persona": persona,
                "wakewords": [],
                "persona_file": persona_file,
            }
        )

        return (
            persona_handler.ai_name,
            persona_handler.persona,
        )

    def is_using_character(
        self,
        fn_get_character_list: typing.Callable[[], typing.List[str]],
    ) -> bool:
        # get the filename out of the settings.  If it is
        # not empty, make sure it's one of the options in the
        # dropdown.
        persona_file = self.bot.settings.persona_settings.get_str("persona_file")
        if not persona_file:
            return False
        character_name = (
            input_handlers.CharacterComponentToSetting.filename_to_character_name(
                persona_file,
                fn_get_character_list,
            ),
        )
        return "" != character_name

    def get_settings_as_yaml(self) -> str:
        """
        Returns the settings as a yaml string.  The settings
        are whatever is in the settings object.  If you want
        to reflect what is in the UI first, you should call
        save_settings() first.
        """
        io_stream = io.StringIO()
        self.bot.settings.write_to_stream(io_stream)
        return io_stream.getvalue()

    def set_settings_from_yaml(self, yaml_str: str) -> typing.Optional[str]:
        """
        Sets the settings from a yaml string.  This will
        overwrite whatever is in the settings object.

        Returns: None if successful, otherwise an error message
        """

        if self.is_running():
            raise RuntimeError("Cannot set settings while running")

        return self.bot.settings.load_from_yaml_stream(io.StringIO(yaml_str))
