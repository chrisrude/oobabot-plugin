import abc
import typing

import gradio as gr
import oobabot
import oobabot.overengineered_settings_parser
import oobabot.settings

import modules

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
    def write_to_settings(self, new_value: typing.List[str]) -> None:
        # todo: map name to file path
        super().write_to_settings("")

    def read_from_settings(self) -> typing.List[str]:
        # todo: map file path to name
        # add in the choices element, which is the list of available characters
        # to choose from
        return super().read_from_settings()

    def init_component_from_setting(self):
        def init_component():
            self.component.update(
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
        print(f"reading from settings {self.setting_name}")
        wake_words = self.settings_group.get_list(self.setting_name)
        print(f"got wake words {wake_words}")
        s = ", ".join(wake_words)
        print(f"returning {s}")
        return s


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
        # CharacterComponentToSetting(
        #     oobabot_layout.character_dropdown,
        #     settings.persona_settings,
        #     "persona_file",
        # ),
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
        # todo: discord behavior checkbox group
    ]
    # make a map from component to setting
    return {c.component: c for c in components_to_settings}
