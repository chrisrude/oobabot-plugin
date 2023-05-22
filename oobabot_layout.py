import gradio as gr

from . import oobabot_constants


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

    def setup_ui(
        self,
        get_logs: callable,
        has_plausible_token: bool,
    ) -> None:
        with gr.Blocks():
            with gr.Row(elem_id="oobabot-tab"):
                with gr.Column(min_width=450, scale=1):  # settings column
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
                    gr.Markdown("### Discord Behavior")
                    with gr.Column():
                        self._init_discord_behavior_widgets()

                with gr.Column(scale=2):  # runtime status column
                    self._init_runtime_widgets(get_logs)

    def _init_token_widgets(
        self,
    ) -> None:
        gr.Markdown(
            oobabot_constants.INSTRUCTIONS_PART_1_MD,
            elem_classes=["oobabot_instructions"],
        )
        with gr.Row():
            self.discord_token_textbox = gr.Textbox(
                label="Discord Token",
                show_label=False,
                placeholder="Paste your Discord bot token here.",
                value=" ",  # this is terrible
            )
            self.discord_token_save_button = gr.Button(
                value="💾", elem_id="oobabot-save-token"
            )
        gr.Markdown(
            oobabot_constants.INSTRUCTIONS_PART_2_MD,
            elem_classes=["oobabot_instructions"],
        )
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
