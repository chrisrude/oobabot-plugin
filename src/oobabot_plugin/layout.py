# -*- coding: utf-8 -*-
"""
This lays out the structure of the oobabot UI.
It contains no behavior, only defining the UI components.
"""

import typing

import gradio as gr

from oobabot_plugin import strings


class OobabotLayout:
    """
    This class is responsible for creating the oobabot UI frame.

    It should create all of the UI components, but not set any
    behaviors or values.
    """

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

    # stable diffusion settings
    stable_diffusion_url_textbox: gr.Textbox
    stable_diffusion_prefix: gr.Textbox

    save_settings_button: gr.Button

    def layout_ui(
        self,
        get_logs: typing.Callable[[], str],
        has_plausible_token: bool,
        stable_diffusion_keywords: typing.List[str],
        api_extension_loaded: bool,
    ) -> None:
        with gr.Blocks():
            with gr.Row(elem_id="oobabot-tab"):
                with gr.Column(min_width=400, scale=1):  # settings column
                    self.welcome_accordion = gr.Accordion(
                        "Set Discord Token",
                        elem_id="discord_bot_token_accordion",
                        open=not has_plausible_token,
                    )
                    with self.welcome_accordion:
                        self._init_token_widgets()
                    gr.Markdown("### Oobabot Persona")
                    with gr.Column(scale=0):
                        self._init_persona_widgets()
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Discord Behavior")
                            self._init_discord_behavior_widgets()
                        with gr.Column():
                            gr.Markdown("### Stable Diffusion (optional)")
                            self._init_stable_diffusion_widgets(
                                stable_diffusion_keywords
                            )
                            self.save_settings_button = gr.Button(
                                value="💾 Save Settings",
                                elem_id="oobabot-save-settings",
                            )

                with gr.Column(scale=2):  # runtime status column
                    self._init_runtime_widgets(get_logs, api_extension_loaded)

    def _init_token_widgets(self) -> None:
        instructions_1, instructions_2 = strings.get_instructions_markdown()
        gr.Markdown(instructions_1, elem_classes=["oobabot_instructions"])
        with gr.Row():
            self.discord_token_textbox = gr.Textbox(
                label="Discord Token",
                show_label=False,
                placeholder="Paste your Discord bot token here.",
                value=" ",  # ugh. this is so gradio fires a change when the value's set
            )
            self.discord_token_save_button = gr.Button(
                value="💾 Save", elem_id="oobabot-save-token"
            )
        gr.Markdown(instructions_2, elem_classes=["oobabot_instructions"])
        self.discord_invite_link_html = gr.HTML()
        self.ive_done_all_this_button = gr.Button(
            value="I've Done All This",
            elem_id="oobabot_done_all_this",
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
            interactive=True,
        )
        self.persona_textbox = gr.Textbox(
            label="Persona",
            info="""
            This prefix will be added in front of every user-supplied
            request.  This is useful for setting up a 'character' for the
            bot to play.
            """,
            interactive=True,
            lines=6,
        )
        self.wake_words_textbox = gr.Textbox(
            label="Wake Words",
            info="""
                One or more words that the bot will listen for.
                The bot will listen in all discord channels it can
                access for one of these words to be mentioned, then reply
                to any messages it sees with a matching word.
                The bot will always reply to @-mentions and
                direct messages, even if no wake words are supplied.
                """,
            interactive=True,
        )

    BY_SENTENCE = "by sentence"
    SINGLE_MESSAGE = "single message"
    STREAMING = "streaming [beta feature]"

    IGNORE_DMS = "Ignore DMs"
    REPLY_IN_THREAD = "Reply in Thread"

    def _init_discord_behavior_widgets(self) -> None:
        self.split_responses_radio_group = gr.Radio(
            [self.BY_SENTENCE, self.SINGLE_MESSAGE, self.STREAMING],
            label="Split Responses",
            info="How should `oobabot` split responses into messages?",
            value=self.BY_SENTENCE,
            interactive=True,
        )
        self.history_lines_slider = gr.Slider(
            label="History Lines",
            minimum=1,
            maximum=30,
            value=7,
            step=1,
            info="Number of lines of chat history the AI will see when generating "
            + "a response",
            interactive=True,
        )

        self.discord_behavior_checkbox_group = gr.CheckboxGroup(
            [self.IGNORE_DMS, self.REPLY_IN_THREAD],
            label="Behavior Adjustments",
            info=(
                f"{self.IGNORE_DMS} = don't reply to direct messages.  "
                + f"{self.REPLY_IN_THREAD} = create a new thread for each response "
                + "in a public channel."
            ),
            interactive=True,
        )

    def _init_stable_diffusion_widgets(
        self, stable_diffusion_keywords: typing.List[str]
    ) -> None:
        self.stable_diffusion_url_textbox = gr.Textbox(
            label="Stable Diffusion URL",
            info=(
                "When this is set, the bot will contact Stable Diffusion to generate "
                + "images and post them to Discord.  If the bot finds one of these "
                + "words in a message, it will respond with an image: "
                + ", ".join(stable_diffusion_keywords)
            ),
            max_lines=1,
            interactive=True,
        )
        self.stable_diffusion_prefix = gr.Textbox(
            label="Stable Diffusion Prefix",
            info=(
                "This prefix will be added in front of every user-supplied image "
                + "request.  This is useful for setting up a 'character' for the "
                + "bot to play."
            ),
            interactive=True,
        )

    def _init_runtime_widgets(
        self,
        get_logs: typing.Callable[[], str],
        api_extension_loaded: bool,
    ) -> None:
        with gr.Row():
            self.start_button = gr.Button(
                value="Start Oobabot",
                interactive=False,
            )
            self.stop_button = gr.Button(
                value="Stop Oobabot",
                interactive=False,
            )
        gr.Markdown("### Oobabot Status", elem_id="oobabot-status-heading")
        if not api_extension_loaded:
            gr.Markdown(
                "**Warning**: The API extension is not loaded.  "
                + "`Oobabot` will not work unless it is enabled.",
                elem_id="oobabot-api-not-loaded",
            )
        with gr.Row():
            self.log_output_html = gr.HTML(
                label="Oobabot Log",
                value=get_logs,
                every=0.5,
                elem_classes=["oobabot-output"],
            )
