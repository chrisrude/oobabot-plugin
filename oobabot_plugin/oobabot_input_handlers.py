# -*- coding: utf-8 -*-
import abc
import pathlib
import typing

import gradio as gr
import modules

import oobabot
import oobabot.overengineered_settings_parser
import oobabot.settings

from . import oobabot_layout


class ComponentToSetting(abc.ABC):
    def __init__(self, component: gr.components.IOComponent):
        self.component = component

    @abc.abstractmethod
    def write_to_settings(self, _new_value: str) -> None:
        """
        Takes the current value of the component and writes
        it to the setting group
        """
        ...

    @abc.abstractmethod
    def read_from_settings(self) -> str:
        """
        Takes the current value of the setting and returns
        its value.
        """
        ...

    def init_component_from_setting(self):
        def init_component():
            return self.component.update(
                value=self.read_from_settings(),
                interactive=True,
            )

        self.component.attach_load_event(
            init_component,
            None,
        )

    def update_component_from_event(self, new_value: str) -> dict:
        self.write_to_settings(new_value)
        return self.component.update(value=self.read_from_settings())

    def disabled(self):
        return self.component.update(interactive=False)

    def enabled(self):
        return self.component.update(interactive=True)


class SimpleComponentToSetting(ComponentToSetting):
    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
        setting_name: str,
    ):
        super().__init__(component)
        self.settings_group = settings_group
        self.setting_name = setting_name

    def write_to_settings(self, new_value: typing.Any) -> None:
        self.settings_group.set(self.setting_name, str(new_value).strip())

    def read_from_settings(self) -> str:
        val = self.settings_group.get(self.setting_name)
        return val


class CharacterComponentToSetting(SimpleComponentToSetting):
    FOLDER = "characters"

    def _character_name_to_filepath(self, character: str) -> str:
        # this is how it's done in chat.py... there's no method to
        # call, so just do the same thing here
        filename = ""
        for extension in ["yml", "yaml", "json"]:
            filepath = pathlib.Path(f"{self.FOLDER}/{character}.{extension}")
            if filepath.exists():
                filename = filepath.resolve()
        return filename

    def write_to_settings(self, character_name: str) -> None:
        filename = self._character_name_to_filepath(character_name)
        super().write_to_settings(filename)

    def read_from_settings(self) -> str:
        # turning the path back into the character name just means
        # removing the folder and extension... but case may have been
        # lost, so we'll need to match it against the list of available
        # options.
        # also, the file may no longer exist, in that case we'll just
        # return the empty string
        filename = super().read_from_settings()
        if not filename:
            return ""
        path = pathlib.Path(filename)
        if not path.exists():
            return ""
        characters = modules.utils.get_available_characters()
        for character in characters:
            if character.lower() == path.stem.lower():
                return character
        return ""

    def update_component_from_event(self, new_value: str) -> dict:
        self.write_to_settings(new_value)
        result = self.component.update(
            value=self.read_from_settings(),
            choices=modules.utils.get_available_characters(),
        )
        return result

    def init_component_from_setting(self):
        def init_component():
            return self.component.update(
                value=self.read_from_settings(),
                interactive=True,
                choices=modules.utils.get_available_characters(),
            )

        self.component.attach_load_event(
            init_component,
            None,
        )


class WakewordsComponentToSetting(SimpleComponentToSetting):
    def write_to_settings(self, new_value: str) -> None:
        words = [word.strip() for word in new_value.split(",")]
        self.settings_group.set(self.setting_name, words)

    def read_from_settings(self) -> str:
        wake_words = self.settings_group.get_list(self.setting_name)
        return ", ".join(wake_words)


class ResponseRadioComponentToSetting(ComponentToSetting):
    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
    ):
        super().__init__(component)
        self.settings_group = settings_group

    def _split_radio_group_to_settings(
        self,
        new_value: str,
    ) -> typing.Tuple[bool, bool]:
        dont_split_responses = False
        stream_responses = False
        if new_value == oobabot_layout.OobabotLayout.SINGLE_MESSAGE:
            dont_split_responses = True
        elif new_value == oobabot_layout.OobabotLayout.STREAMING:
            stream_responses = True
        return (dont_split_responses, stream_responses)

    def _settings_to_radio_group_value(
        self,
        dont_split_responses: bool,
        stream_responses: bool,
    ) -> str:
        if dont_split_responses:
            return oobabot_layout.OobabotLayout.SINGLE_MESSAGE
        if stream_responses:
            return oobabot_layout.OobabotLayout.STREAMING
        return oobabot_layout.OobabotLayout.BY_SENTENCE

    def write_to_settings(self, new_value: str) -> None:
        dont_split_responses, stream_responses = self._split_radio_group_to_settings(
            new_value
        )
        self.settings_group.set("dont_split_responses", dont_split_responses)
        self.settings_group.set("stream_responses", stream_responses)

    def read_from_settings(self) -> dict:
        return self._settings_to_radio_group_value(
            self.settings_group.get("dont_split_responses"),
            self.settings_group.get("stream_responses"),
        )


class BehaviorCheckboxGroupToSetting(ComponentToSetting):
    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
    ):
        super().__init__(component)
        self.settings_group = settings_group

    OPTIONS = [
        ("ignore_dms", oobabot_layout.OobabotLayout.IGNORE_DMS),
        ("reply_in_thread", oobabot_layout.OobabotLayout.REPLY_IN_THREAD),
    ]

    def write_to_settings(self, new_values: typing.List[str]) -> None:
        # we'll get a list of strings reflecting the values of the
        # checked boxes in the group
        for option_setting, option_ui_string in self.OPTIONS:
            value = option_ui_string in new_values
            self.settings_group.set(option_setting, value)

    def read_from_settings(self) -> typing.List[str]:
        options_on = []
        for option_setting, option_ui_string in self.OPTIONS:
            if self.settings_group.get(option_setting):
                options_on.append(option_ui_string)
        return options_on


def get_all(
    oobabot_layout: oobabot_layout.OobabotLayout,
    settings: oobabot.settings.Settings,
) -> dict[gr.components.IOComponent, ComponentToSetting]:
    components_to_settings = [
        SimpleComponentToSetting(
            oobabot_layout.discord_token_textbox,
            settings.discord_settings,
            "discord_token",
        ),
        CharacterComponentToSetting(
            oobabot_layout.character_dropdown,
            settings.persona_settings,
            "persona_file",
        ),
        SimpleComponentToSetting(
            oobabot_layout.ai_name_textbox,
            settings.persona_settings,
            "ai_name",
        ),
        SimpleComponentToSetting(
            oobabot_layout.persona_textbox,
            settings.persona_settings,
            "persona",
        ),
        WakewordsComponentToSetting(
            oobabot_layout.wake_words_textbox,
            settings.persona_settings,
            "wakewords",
        ),
        ResponseRadioComponentToSetting(
            oobabot_layout.split_responses_radio_group,
            settings.discord_settings,
        ),
        SimpleComponentToSetting(
            oobabot_layout.history_lines_slider,
            settings.discord_settings,
            "history_lines",
        ),
        BehaviorCheckboxGroupToSetting(
            oobabot_layout.discord_behavior_checkbox_group,
            settings.discord_settings,
        ),
        SimpleComponentToSetting(
            oobabot_layout.stable_diffusion_url_textbox,
            settings.stable_diffusion_settings,
            "stable_diffusion_url",
        ),
        SimpleComponentToSetting(
            oobabot_layout.stable_diffusion_prefix,
            settings.stable_diffusion_settings,
            "extra_prompt_text",
        ),
    ]
    # make a map from component to setting
    return {c.component: c for c in components_to_settings}
