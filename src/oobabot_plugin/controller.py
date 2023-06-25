# -*- coding: utf-8 -*-
"""
Controller for the oobabot UI plugin.  Contains
all behavior for the UI, but no UI components.
"""

from oobabot_plugin import button_enablers
from oobabot_plugin import button_handlers
from oobabot_plugin import layout
from oobabot_plugin import strings
from oobabot_plugin import transcript_view
from oobabot_plugin import worker


class OobabotController:
    """
    Controller for the oobabot UI plugin.  Contains
    all behavior for the UI, but no UI components
    or state.
    """

    def __init__(
        self,
        port: int,
        config_file: str,
        api_extension_loaded: bool,
    ):
        self.layout = layout.OobabotLayout()
        self.worker = worker.OobabotWorker(port, config_file, self.layout)
        self.api_extension_loaded = api_extension_loaded

    ##################################
    # oobabooga <> extension interface

    def init_ui(self) -> None:
        """
        Creates custom gradio elements when the UI is launched.
        """

        token = self.worker.bot.settings.discord_settings.get_str("discord_token")
        plausible_token = strings.token_is_plausible(token)
        image_words = self.worker.bot.settings.stable_diffusion_settings.get_list(
            "image_words"
        )
        stable_diffusion_keywords = [str(x) for x in image_words]

        is_using_character = self.worker.is_using_character(
            strings.get_available_characters,
        )

        self.layout.layout_ui(
            get_logs=self.worker.get_logs,
            has_plausible_token=plausible_token,
            stable_diffusion_keywords=stable_diffusion_keywords,
            api_extension_loaded=self.api_extension_loaded,
            is_using_character=is_using_character,
            get_transcript_html=lambda: transcript_view.get_transcript_html(
                self.worker.get_transcript,
                self.worker.get_fancy_author,
            ),
            is_voice_enabled=self.worker.is_voice_enabled(),
        )

        # create our own handlers for every input event which will map
        # between our settings object and its corresponding UI component

        # for all input components, add initialization handlers to
        # set their values from what we read from the settings file
        for component_to_setting in self.worker.get_input_handlers(
            strings.get_available_characters
        ).values():
            component_to_setting.init_component_from_setting()

        # sets up what happens when each button is pressed
        button_handlers.ButtonHandlers(is_using_character, self.layout, self.worker)

        # enables or disables buttons based on the state of other inputs
        button_enablers.init_enablers(self.layout, token, self.worker, plausible_token)

        # start the bot if the setting is enabled
        if self.worker.bot.settings.oobabooga_settings.get("plugin_auto_start"):
            self.worker.start()
