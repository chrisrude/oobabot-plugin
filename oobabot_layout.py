import typing

import gradio as gr
from oobabot import oobabot

import modules

from . import oobabot_constants


class OobabotLayout:
    # discord token widgets
    welcome_accordion: gr.Accordion
    discord_token_textbox: gr.Textbox
    discord_token_save_button: gr.Button
    discord_invite_link_html: gr.HTML
    ive_done_all_this_button: gr.Button

    # persona widgets
    character_dropdown: gr.Dropdown
    reload_character_button: gr.Button

    ai_name_textbox: gr.Textbox
    persona_textbox: gr.Textbox
    wake_words_textbox: gr.Textbox

    # discord behavior widgets
    split_responses_radio_group: gr.Radio
    history_lines_slider: gr.Slider
    discord_behavior_checkbox_group: gr.CheckboxGroup

    # runtime widgets
    start_button: gr.Button
    stop_button: gr.Button
    log_output_html: gr.HTML

    def set_ui_from_settings(
        self,
        settings: oobabot.settings.Settings,
    ):
        """applies the values in settings to the UI elements"""

        token = settings.discord_settings.get_str("discord_token")
        self.discord_token_textbox.value = token
        self.character_dropdown.choices = modules.utils.get_available_characters()
        self.ai_name_textbox.value = settings.persona_settings.get_str("ai_name")
        self.persona_textbox.value = settings.persona_settings.get_str("persona")

        # self.wake_words_textbox.value = ", ".join(
        #     settings.persona_settings.get_list("wakewords")
        # )
        # split_responses_radio_group: gr.Radio
        self.history_lines_slider.value = settings.discord_settings.get("history_lines")
        # discord_behavior_checkbox_group: gr.CheckboxGroup

    def set_settings_from_ui(self, settings: oobabot.settings.Settings):
        """takes the current UI elements and applies them to settings"""

    def disable_all(self) -> None:
        # loop through all elements, and for ones that are a
        # subclass of gradio.Component, set interactive to False
        for elem in self.__dict__.values():
            if isinstance(elem, gr.components.IOComponent):
                elem.interactive = False

    def set_all_setting_widgets_interactive(self, interactive: bool):
        self.character_dropdown.interactive = interactive
        self.reload_character_button.interactive = interactive
        self.ai_name_textbox.interactive = interactive
        self.persona_textbox.interactive = interactive
        self.wake_words_textbox.interactive = interactive
        self.split_responses_radio_group.interactive = interactive
        self.history_lines_slider.interactive = interactive
        self.discord_behavior_checkbox_group.interactive = interactive

    def setup_ui(
        self,
        on_ui_change: callable,
        get_logs: callable,
        bot: oobabot.Oobabot,
        settings: oobabot.settings.Settings,
    ) -> None:
        with gr.Blocks():
            with gr.Row(elem_id="oobabot-tab"):
                with gr.Column(min_width=450, scale=1):  # settings column
                    self.welcome_accordion = gr.Accordion(
                        "Set Discord Token", elem_id="discord_bot_token_accordion"
                    )
                    with self.welcome_accordion:
                        self._init_token_widgets(
                            settings=settings,
                            bot=bot,
                            on_ui_change=on_ui_change,
                        )
                    gr.Markdown("### Oobabot Persona")
                    with gr.Column(scale=0):
                        self._init_persona_widgets()
                    gr.Markdown("### Discord Behavior")
                    with gr.Column():
                        self._init_discord_behavior_widgets()

                with gr.Column(scale=2):  # runtime status column
                    self._init_runtime_widgets(get_logs)

    def _init_token_widgets(
        self,
        settings: oobabot.settings.Settings,
        bot: oobabot.Oobabot,
        on_ui_change: callable,
    ) -> None:
        token = settings.discord_settings.get_str("discord_token")
        gr.Markdown(
            oobabot_constants.INSTRUCTIONS_PART_1_MD,
            elem_classes=["oobabot_instructions"],
        )
        with gr.Row():
            self.discord_token_textbox = gr.Textbox(
                label="Discord Token",
                value=token,
            )
            self.discord_token_save_button = gr.Button(
                value="💾", elem_id="oobabot-save-token"
            )
        gr.Markdown(
            oobabot_constants.INSTRUCTIONS_PART_2_MD,
            elem_classes=["oobabot_instructions"],
        )
        self.discord_invite_link_html = gr.HTML(
            value=make_link_from_token(token, bot.generate_invite_url),
        )
        self.ive_done_all_this_button = gr.Button(
            value="I've Done All This",
            elem_id="oobabot_done_all_this",
        )

        def on_save_button(new_token: str):
            link = ""
            if new_token:
                valid = bot.test_discord_token(new_token)
                if valid:
                    settings.discord_settings.get_setting("discord_token").set_value(
                        new_token
                    )
                    link = "🟢 Your token works!<br/>" + make_link_from_token(
                        new_token, bot.generate_invite_url
                    )
                else:
                    link = "❌ The token you entered is invalid."
            on_ui_change()
            return link

        self.discord_token_save_button.click(
            on_save_button,
            inputs=[self.discord_token_textbox],
            outputs=[self.discord_invite_link_html],
        )

    def _init_persona_widgets(self) -> None:
        with gr.Row():
            self.character_dropdown = gr.Dropdown(
                label="Character",
                info="Used in chat and chat-instruct modes.",
            )
            self.reload_character_button = gr.Button(
                value="↻",
                elem_id="oobabot-refresh-character-menu",
            )

        self.ai_name_textbox = gr.Textbox(
            label="AI Name",
            info="Name the AI will use to refer to itself",
        )
        self.persona_textbox = gr.Textbox(
            label="Persona",
            info="""
            This prefix will be added in front of every user-supplied
            request.  This is useful for setting up a 'character' for the
            bot to play.
            """,
            lines=12,
        )
        self.wake_words_textbox = gr.Textbox(
            label="Wake Words",
            info="""
                One or more words that the bot will listen for.
                The bot will listen in all discord channels can
                access for one of these words to be mentioned, then reply
                to any messages it sees with a matching word.
                The bot will always reply to @-mentions and
                direct messages, even if no wake words are supplied.
                """,
        )

    def _init_discord_behavior_widgets(self) -> None:
        self.split_responses_radio_group = gr.Radio(
            ["by sentence", "single message", "streaming [beta feature]"],
            label="Split Responses",
            info="How should `oobabot` split responses into messages?",
            value="by sentence",
        )
        self.history_lines_slider = gr.Slider(
            label="History Lines",
            minimum=1,
            maximum=30,
            value=7,
            step=1,
            info="Number of lines of chat history the AI will see when generating "
            + "a response",
        )
        self.discord_behavior_checkbox_group = gr.CheckboxGroup(
            ["Ignore DMs", "Reply in Thread"],
            label="Behavior Adjustments",
            info="Ignore DMs = don't reply to direct messages.  Reply in Thread = "
            + "create a new thread for each response in a public channel.",
        )

    def _init_runtime_widgets(self, get_logs: callable) -> None:
        with gr.Row():
            self.start_button = gr.Button(value="Start Oobabot")
            self.stop_button = gr.Button(value="Stop Oobabot")
        gr.Markdown("### Oobabot Status", elem_id="oobabot-status-heading")
        with gr.Row():
            self.log_output_html = gr.HTML(
                label="Oobabot Log",
                value=get_logs,
                every=0.5,
                elem_classes=["oobabot-output"],
            )


def make_link_from_token(
    token: str, fn_calc_invite_url: typing.Optional[callable]
) -> str:
    if not token or not fn_calc_invite_url:
        return "A link will appear here once you have set your Discord token."
    link = fn_calc_invite_url(token)
    print("link", link)
    return (
        f'<a href="{link}" target="_blank">Click here to invite your bot</a> '
        + "to a Discord server."
    )
