# -*- coding: utf-8 -*-
"""
Classes for managing the interaction between gradio input
components and oobabot settings.
"""


import abc
import pathlib
import typing

import gradio as gr
import oobabot.overengineered_settings_parser


class ComponentToSetting(abc.ABC):
    """
    This class is responsible for managing the interaction between
    a gradio component and a setting in the settings file.
    """

    def __init__(self, component: gr.components.IOComponent):
        self.component = component

    @abc.abstractmethod
    def write_to_settings(self, _new_value: str) -> None:
        """
        Takes the current value of the component and writes
        it to the setting group
        """

    @abc.abstractmethod
    def read_from_settings(self) -> str:
        """
        Takes the current value of the setting and returns
        its value.
        """

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
    """
    A basic implementation of ComponentToSetting that handles
    settings that are just a 1:1 mapping to a single string,
    int, or bool value.
    """

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

    def read_from_settings(
        self,
    ) -> oobabot.overengineered_settings_parser.SettingValueType:
        val = self.settings_group.get(self.setting_name)
        return val


class CharacterComponentToSetting(SimpleComponentToSetting):
    """
    A specific implementation of SimpleComponentToSetting that
    handles the character setting.  "Characters" are just
    files in the ./characters folder, without extensions.
    This class attempts to match the behavior of chat.py's
    character selection.
    """

    FOLDER = "characters"

    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
        setting_name: str,
        fn_get_character_list: typing.Callable[[], typing.List[str]],
    ):
        super().__init__(component, settings_group, setting_name)
        self.fn_get_character_list = fn_get_character_list

    def _character_name_to_filepath(self, character: str) -> str:
        # this is how it's done in chat.py... there's no method to
        # call, so just do the same thing here
        filename = ""
        for extension in ["yml", "yaml", "json"]:
            filepath = pathlib.Path(f"{self.FOLDER}/{character}.{extension}")
            if filepath.exists():
                filename = str(filepath.resolve())
        return filename

    def write_to_settings(self, new_value: str) -> None:
        filename = self._character_name_to_filepath(new_value)
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
        path = pathlib.Path(str(filename))
        if not path.exists():
            return ""
        characters = self.fn_get_character_list()
        for character in characters:
            if character.lower() == path.stem.lower():
                return character
        return ""

    def update_component_from_event(self, new_value: str) -> dict:
        self.write_to_settings(new_value)
        result = self.component.update(
            value=self.read_from_settings(),
            choices=self.fn_get_character_list(),
        )
        return result

    def init_component_from_setting(self):
        def init_component():
            return self.component.update(
                value=self.read_from_settings(),
                interactive=True,
                choices=self.fn_get_character_list(),
            )

        self.component.attach_load_event(
            init_component,
            None,
        )


class ListComponentToSetting(SimpleComponentToSetting):
    """
    A specific implementation of SimpleComponentToSetting that
    handles settings that are lists of strings.
    """

    def write_to_settings(self, new_value: str) -> None:
        words = [word.strip() for word in new_value.split(",")]
        self.settings_group.set(self.setting_name, words)

    def read_from_settings(self) -> str:
        word_list = self.settings_group.get_list(self.setting_name)
        word_list = [str(word).strip() for word in word_list]
        return ", ".join(word_list)


class ResponseRadioComponentToSetting(ComponentToSetting):
    """
    A specific implementation of ComponentToSetting that
    handles the radio button group for how we split
    responses into messages.  There are currently 3
    radio options, and 2 binary flags we will set.
    """

    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
        single_message_label: str,
        streaming_label: str,
        by_sentence_label: str,
    ):
        super().__init__(component)
        self.settings_group = settings_group
        self.single_message_label = single_message_label
        self.streaming_label = streaming_label
        self.by_sentence_label = by_sentence_label

    def _split_radio_group_to_settings(
        self,
        new_value: str,
    ) -> typing.Tuple[bool, bool]:
        dont_split_responses = False
        stream_responses = False
        if new_value == self.single_message_label:
            dont_split_responses = True
        elif new_value == self.streaming_label:
            stream_responses = True
        return (dont_split_responses, stream_responses)

    def _settings_to_radio_group_value(
        self,
        dont_split_responses: bool,
        stream_responses: bool,
    ) -> str:
        if dont_split_responses:
            return self.single_message_label
        if stream_responses:
            return self.streaming_label
        return self.by_sentence_label

    def write_to_settings(self, new_value: str) -> None:
        dont_split_responses, stream_responses = self._split_radio_group_to_settings(
            new_value
        )
        self.settings_group.set("dont_split_responses", dont_split_responses)
        self.settings_group.set("stream_responses", stream_responses)

    def read_from_settings(self) -> str:
        return self._settings_to_radio_group_value(
            bool(self.settings_group.get("dont_split_responses")),
            bool(self.settings_group.get("stream_responses")),
        )


class CheckboxGroupToSetting(ComponentToSetting):
    """
    A generic implementation of ComponentToSetting that
    handles a group of checkboxes.  The checkboxes are
    identified by a list of strings, and each setting
    is a boolean value.
    """

    def __init__(
        self,
        component: gr.components.IOComponent,
        settings_group: oobabot.overengineered_settings_parser.ConfigSettingGroup,
        options: typing.List[typing.Tuple[str, str]],
    ):
        super().__init__(component)
        self.settings_group = settings_group
        self.options = options

    def write_to_settings(self, new_values: typing.List[str]) -> None:
        # we'll get a list of strings reflecting the values of the
        # checked boxes in the group
        for option_setting, option_ui_string in self.options:
            value = option_ui_string in new_values
            self.settings_group.set(option_setting, value)

    def read_from_settings(self) -> typing.List[str]:
        options_on = []
        for option_setting, option_ui_string in self.options:
            if self.settings_group.get(option_setting):
                options_on.append(option_ui_string)
        return options_on
