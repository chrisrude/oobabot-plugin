# -*- coding: utf-8 -*-
"""
This lays out the structure of the oobabot UI.
It contains no behavior, only defining the UI components.
"""

import textwrap
import typing

import gradio as gr

from oobabot_plugin import strings


class OobabotLayout:
    """
    This class is responsible for creating the oobabot UI frame.

    It should create all of the UI components, but not set any
    behaviors or values.
    """

    def __init__(self) -> None:
        # outer navigation elements
        self.tab_config: gr.Tab
        self.tab_audio: typing.Optional[gr.Tab]
        self.tab_advanced: gr.Tab

        #############################################
        # Configuration tab
        #############################################

        # discord token widgets
        self.welcome_accordion: gr.Accordion
        self.discord_token_textbox: gr.Textbox
        self.discord_token_save_button: gr.Button
        self.discord_invite_link_html: gr.HTML
        self.ive_done_all_this_button: gr.Button

        # persona widgets
        self.character_dropdown: gr.Dropdown

        self.ai_name_textbox: gr.Textbox
        self.persona_textbox: gr.Textbox

        # the _character ones are only shown when we are
        # using a character, when they're shown, the other
        # ones are hidden.
        self.ai_name_textbox_character: gr.Textbox
        self.persona_textbox_character: gr.Textbox

        self.wake_words_textbox: gr.Textbox

        # discord behavior widgets
        self.split_responses_radio_group: gr.Radio
        self.history_lines_slider: gr.Slider
        self.discord_behavior_checkbox_group: gr.CheckboxGroup

        # stable diffusion settings
        self.stable_diffusion_url_textbox: gr.Textbox
        self.stable_diffusion_prefix: gr.Textbox
        self.stable_diffusion_params: gr.Textbox

        self.save_settings_button: gr.Button

        #############################################
        # Advanced tab
        #############################################

        self.advanced_save_result: gr.Markdown
        self.advanced_save_settings_button: gr.Button
        self.advanced_yaml_editor: gr.Code

        #############################################
        # Audio tab
        #############################################

        self.transcript_markdown: typing.Optional[gr.Markdown]
        self.transcript_html: typing.Optional[gr.HTML]

        #############################################
        # Runtime section
        #############################################

        # runtime widgets
        self.status_html: gr.HTML
        self.start_button: gr.Button
        self.plugin_auto_start_checkbox: gr.Checkbox
        self.stop_button: gr.Button
        self.log_etag_textbox: gr.Textbox
        self.log_output_html: gr.HTML
        self.running_state_textbox: gr.Textbox

    def layout_ui(
        self,
        get_log_etag: typing.Callable[[], int],
        has_plausible_token: bool,
        stable_diffusion_keywords: typing.List[str],
        api_extension_loaded: bool,
        is_using_character: bool,
        get_transcript_html: typing.Callable[[], str],
        is_voice_enabled: bool,
    ) -> None:
        with gr.Blocks():
            self.tab_config = gr.Tab(
                label="Configuration",
                elem_id="oobabot-tab-config",
            )
            self.tab_advanced = gr.Tab(
                label="Advanced",
                elem_id="oobabot-tab-advanced",
            )
            if is_voice_enabled:
                self.tab_audio = gr.Tab(
                    label="Audio",
                    elem_id="oobabot-tab-audio",
                )
            else:
                self.tab_audio = None

            with self.tab_config:
                with gr.Row():
                    with gr.Column(min_width=400):
                        self._init_config_ui(
                            has_plausible_token,
                            stable_diffusion_keywords,
                            is_using_character,
                        )
                    with gr.Column(scale=2):
                        self._init_runtime_ui(
                            get_log_etag,
                            api_extension_loaded,
                        )

            with self.tab_advanced:
                self._init_advanced_ui()

            if self.tab_audio is None:
                self.transcript_markdown = None
                self.transcript_html = None
            else:
                with self.tab_audio:
                    with gr.Column():
                        self.transcript_markdown = gr.Markdown(
                            strings.get_transcript_markdown(),
                            elem_classes="oobabot-transcript-markdown",
                        )
                        self.transcript_html = gr.HTML(
                            label="Oobabot Transcript",
                            value=get_transcript_html,
                            every=strings.QUICK_UPDATE_INTERVAL_SECONDS,
                            elem_classes=["oobabot-audio-output"],
                        )

    #############################################
    # Configuration tab
    #############################################

    BY_SENTENCE = "by sentence"
    SINGLE_MESSAGE = "single message"
    STREAMING = "streaming [beta feature]"

    IGNORE_DMS = "Ignore DMs"
    REPLY_IN_THREAD = "Reply in Thread"

    def _init_config_ui(
        self,
        has_plausible_token: bool,
        stable_diffusion_keywords: typing.List[str],
        is_using_character: bool,
    ) -> None:
        def _init_token_widgets() -> None:
            self.welcome_accordion = gr.Accordion(
                "Set Discord Token",
                elem_id="discord_bot_token_accordion",
                open=not has_plausible_token,
            )
            with self.welcome_accordion:
                instructions_1, instructions_2 = strings.get_instructions_markdown()
                gr.Markdown(instructions_1, elem_classes=["oobabot_instructions"])
                with gr.Row():
                    self.discord_token_textbox = gr.Textbox(
                        label="Discord Token",
                        show_label=False,
                        placeholder="Paste your Discord bot token here.",
                        # ugh. this is so gradio fires a change when the value's set
                        value=" ",
                        elem_id="oobabot-token-textbox",
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

        def _init_persona_ui() -> None:
            gr.Markdown("### Oobabot Persona")
            with gr.Column(scale=0):
                with gr.Row():
                    self.character_dropdown = gr.Dropdown(
                        label="Character",
                        info="Used in chat and chat-instruct modes.",
                        elem_id="oobabot-character-dropdown",
                    )

                self.ai_name_textbox = gr.Textbox(
                    label="AI Name",
                    info="Name the AI will use to refer to itself",
                    interactive=True,
                    visible=not is_using_character,
                    elem_id="oobabot-ai-name",
                )
                self.persona_textbox = gr.Textbox(
                    label="Persona",
                    info=textwrap.dedent(
                        """
                        This prefix will be added in front of every user-supplied
                         request.  This is useful for setting up a 'character' for the
                         bot to play.
                        """
                    ),
                    interactive=True,
                    lines=6,
                    visible=not is_using_character,
                    elem_id="oobabot-persona",
                )

                self.ai_name_textbox_character = gr.Textbox(
                    label="AI Name",
                    info="Name the AI will use to refer to itself",
                    interactive=False,
                    visible=is_using_character,
                    elem_id="oobabot-ai-name-character",
                )
                self.persona_textbox_character = gr.Textbox(
                    label="Persona",
                    info=textwrap.dedent(
                        """
                        This prefix will be added in front of every user-supplied
                         request.  This is useful for setting up a 'character' for the
                         bot to play.
                        """
                    ),
                    interactive=False,
                    lines=6,
                    visible=is_using_character,
                    elem_id="oobabot-persona-character",
                )

                self.wake_words_textbox = gr.Textbox(
                    label="Wake Words",
                    info=textwrap.dedent(
                        """
                        One or more words that the bot will listen for.
                         The bot will listen in all discord channels it can
                         access for one of these words to be mentioned, then reply
                         to any messages it sees with a matching word.
                         The bot will always reply to @-mentions and
                         direct messages, even if no wake words are supplied.
                         Separate words with commas.
                        """
                    ),
                    interactive=True,
                    placeholder="e.g.: oobabot, ooba bot, ooba-bot",
                    elem_id="oobabot-wake-words",
                )

        def _init_discord_behavior_widgets() -> None:
            gr.Markdown("### Discord Behavior")

            self.split_responses_radio_group = gr.Radio(
                [self.BY_SENTENCE, self.SINGLE_MESSAGE, self.STREAMING],
                label="Split Responses",
                info="How should `oobabot` split responses into messages?",
                value=self.BY_SENTENCE,
                interactive=True,
                elem_id="oobabot-split-responses",
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
                elem_id="oobabot-history-lines",
            )

            self.discord_behavior_checkbox_group = gr.CheckboxGroup(
                [self.IGNORE_DMS, self.REPLY_IN_THREAD],
                label="Behavior Adjustments",
                info=(
                    f"{self.IGNORE_DMS} = don't reply to direct messages.  "
                    + f"{self.REPLY_IN_THREAD} = create a new thread for each "
                    + "response in a public channel."
                ),
                interactive=True,
                elem_id="oobabot-behavior-adjustments",
            )

        def _init_stable_diffusion_widgets() -> None:
            gr.Markdown("### Stable Diffusion (optional)")

            self.stable_diffusion_url_textbox = gr.Textbox(
                label="Stable Diffusion URL",
                info=textwrap.dedent(
                    (
                        "When this is set, the bot will contact Stable Diffusion to "
                        + "generate images and post them to Discord.  If the bot "
                        + "finds one of these words in a message, it will respond "
                        + "with an image: , ".join(stable_diffusion_keywords)
                    )
                ),
                max_lines=1,
                interactive=True,
                elem_id="oobabot-stable-diffusion-url",
            )
            self.stable_diffusion_prefix = gr.Textbox(
                label="Stable Diffusion Prefix",
                info=textwrap.dedent(
                    """
                    This prefix will be added in front of every user-supplied image
                    request.  This is useful for setting up a 'character' for the
                    bot to play.
                    """
                ),
                interactive=True,
                elem_id="oobabot-stable-diffusion-prefix",
            )

        def _init_save_settings_widgets() -> None:
            self.save_settings_button = gr.Button(
                value="💾 Save Settings",
                elem_id="oobabot-save-settings",
            )

        with gr.Row(elem_id="oobabot-tab"):
            _init_token_widgets()
        with gr.Row():
            with gr.Column():
                _init_persona_ui()
            with gr.Column():
                _init_discord_behavior_widgets()
                _init_stable_diffusion_widgets()
                _init_save_settings_widgets()

    #############################################
    # Advanced tab
    #############################################

    def _init_advanced_ui(self) -> None:
        with gr.Row():
            gr.Markdown(
                textwrap.dedent(
                    """
                    ### Advanced Settings

                    Did you know that there are many more options
                    available to adjust the behavior of your bot?
                    """
                )
            )
            self.advanced_save_result = gr.Markdown(
                elem_id="oobabot-advanced-save-result",
            )
            self.advanced_save_settings_button = gr.Button(
                value="💾 Save Settings",
                elem_id="oobabot-advanced-save-settings",
                interactive=True,
            )
        self.advanced_yaml_editor = gr.Code(
            language="yaml",
        )

    #############################################
    # Runtime tab
    #############################################

    def _init_runtime_ui(
        self,
        get_log_etag: typing.Callable[[], int],
        api_extension_loaded: bool,
    ) -> None:
        with gr.Row():
            self.start_button = gr.Button(
                value="Start Oobabot",
                interactive=False,
            )
            self.plugin_auto_start_checkbox = gr.Checkbox(
                label="Start automatically",
                value=False,
                interactive=True,
                elem_id="oobabot-plugin-auto-start",
            )
            self.stop_button = gr.Button(
                value="Stop Oobabot",
                interactive=False,
            )
            self.running_state_textbox = gr.Textbox(
                "",
                interactive=False,
                visible=False,
                elem_id="oobabot-is-running",
            )

        self.status_html = gr.HTML(
            strings.status_heading(""),
            elem_id="oobabot-status-heading",
        )
        if not api_extension_loaded:
            gr.Markdown(
                "**Warning**: The API extension is not loaded.  "
                + "`Oobabot` will not work unless it is enabled.",
                elem_id="oobabot-api-not-loaded",
            )
        with gr.Row():
            # this value changes every time the log is updated
            # it is used to trigger a full HTML update
            self.log_etag_textbox = gr.Textbox(
                value=get_log_etag,
                every=strings.QUICK_UPDATE_INTERVAL_SECONDS,
                interactive=False,
                visible=False,
                elem_id="oobabot-log-etag",
            )
            self.log_output_html = gr.HTML(
                value="",
                label="Oobabot Log",
                elem_classes=["oobabot-output"],
            )
