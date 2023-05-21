# import ctypes
# import multiprocessing

import os
import threading

import gradio as gr
import modules

from oobabot import oobabot

params = {
    "is_tab": True,
    "activate": True,
    "config_file": "",
}

# can be set in settings.json with:
#   "oobabot-config_file string": "~/oobabot/config.yml",
#
# todo: verify that API extension is running
# todo: automatically use loaded persona


##################################
# oobabot process management
class OobabotWorkerThread:
    ################################################
    # these will run in the oobabooga process
    def __init__(self, port):
        self.thread = None
        self.bot = None
        self.port = port

    def reload(self) -> oobabot.settings.Settings:
        self.stop()
        args = [
            "--config",
            os.path.abspath(params["config_file"]),
            "--base-url",
            f"http://localhost:{self.port}/",
        ]
        self.bot = oobabot.Oobabot(args)
        return self.bot.settings

    def start(self) -> None:
        self.reload()
        self.thread = threading.Thread(target=self.bot.run)
        self.thread.start()

    def stop(self) -> None:
        """
        Stops oobabot.  This is safe to be called
        from any thread.
        """
        if not self.is_running():
            return

        self.bot.stop()
        self.thread.join()
        self.bot = None
        self.thread = None

    def is_running(self) -> bool:
        """
        Returns True if oobabot is running.
        This does not mean that it is connected to discord,
        only that the thread is alive.
        """
        if self.bot is None:
            return False
        if self.thread is None:
            return False
        return self.thread.is_alive()


oobabot_worker_thread = OobabotWorkerThread(modules.shared.args.api_streaming_port)


##################################
# oobabooga <> extension interface


def ui() -> None:
    """
    Creates custom gradio elements when the UI is launched.
    """
    settings = oobabot_worker_thread.reload()
    _init_oobabot_ui(settings)


def custom_css() -> str:
    """
    Returns custom CSS to be injected into the UI.
    """
    return LOG_CSS


INSTRUCTIONS_MD = """
# Welcome to `oobabot`

**`oobabot`** is a Discord bot which can connect this AI with your Discord server.

## Step 1. Create a Bot Account

First, you'll need to generate a Discord bot token.  This is a secret key that
authenticates your bot to Discord.

1. Log in to [Discord's Developer Portal](https://discord.com/developers/applications)
1. Choose **`New Application`**
1. Give your bot a name.  This name will be visible to users.
1. Choose **`Bot`** from the left-hand menu.
1. Under **`Privileged Gateway Intents`** enable:
    - **`SERVER MEMBERS INTENT: ON`**
    - **`MESSAGE CONTENT INTENT: ON`**
1. Hit "Save Changes".
1. Hit **`Reset Token`** and copy the token

## Step 2. Enter your Bot Token

**`Paste your token`** below, then **`Save`**.
"""

INSTRUCTIONS_PART_2_MD = """

## Step 3. Invite your Bot

"""


def _init_token_setup():
    gr.Markdown(INSTRUCTIONS_MD, elem_classes=["oobabot_instructions"])
    with gr.Row():
        token_textbox = gr.Textbox(
            label="Discord Token",
            value="",
        )
        save_button = gr.Button(value="💾", elem_id="oobabot-save-token")
    gr.Markdown(INSTRUCTIONS_PART_2_MD, elem_classes=["oobabot_instructions"])
    invite_url_md = gr.Markdown(
        "**`Click here to invite your bot`** to a Discord server."
    )
    gr.Button(value="I've Done All This", elem_id="oobabot_refresh_invite_url")
    return (token_textbox, save_button, invite_url_md)


def _init_persona_settings(settings: oobabot.settings.Settings):
    with gr.Row():
        character_menu = gr.Dropdown(
            choices=modules.utils.get_available_characters(),
            label="Character",
            info="Used in chat and chat-instruct modes.",
            interactive=True,
        )
        refresh_character_button = gr.Button(
            value="↻",
            elem_id="oobabot-refresh-character-menu",
        )
        # modules.ui.create_refresh_button(
        #     character_menu,
        #     lambda: None,
        #     lambda: {"choices": modules.utils.get_available_characters()},
        #     "refresh-button",
        # )

    gr.Textbox(
        label="AI Name",
        value=settings.persona_settings.get_str("ai_name"),
        info="Name the AI will use to refer to itself",
    )
    gr.Textbox(
        label="Persona",
        value=settings.persona_settings.get_str("persona"),
        info="""
        This prefix will be added in front of every user-supplied
        request.  This is useful for setting up a 'character' for the
        bot to play.
        """,
        lines=12,
    )
    gr.Textbox(
        label="Wake Words",
        value=", ".join(settings.persona_settings.get_list("wakewords")),
        info="""
            One or more words that the bot will listen for.
            The bot will listen in all discord channels can
            access for one of these words to be mentioned, then reply
            to any messages it sees with a matching word.
            The bot will always reply to @-mentions and
            direct messages, even if no wake words are supplied.
            """,
    )


def _init_advanced_settings():
    gr.Radio(
        ["by sentence", "single message", "streaming [beta feature]"],
        label="Split Responses",
        info="How should `oobabot` split responses into messages?",
        value="by sentence",
    ),
    gr.Slider(
        label="History Lines",
        minimum=1,
        maximum=30,
        value=7,
        info="Number of lines of chat history the AI will see when generating a response",
    )
    gr.CheckboxGroup(
        ["Ignore DMs", "Reply in Thread"],
        label="Behavior Adjustments",
        info="Ignore DMs = don't reply to direct messages.  Reply in Thread = create a new thread for each response in a public channel.",
    )


def _init_oobabot_ui(settings: oobabot.settings.Settings) -> None:
    token = settings.discord_settings.get_str("discord_token")
    has_token = token is not None and len(token) > 0
    has_token = False
    is_running = False
    with gr.Blocks():
        with gr.Row(elem_id="oobabot-tab"):
            with gr.Column(min_width=450, scale=1):  # settings column
                with gr.Accordion(
                    "", open=not has_token, elem_id="discord_bot_token_accordion"
                ):
                    # when closed, change text to "Discord Bot Token"
                    _init_token_setup()
                gr.Markdown("### Oobabot Persona")
                with gr.Column(scale=0):
                    _init_persona_settings(settings=settings)
                gr.Markdown("### Discord Behavior")
                with gr.Column():
                    _init_advanced_settings()

            with gr.Column(scale=2):  # runtime status column
                with gr.Row():
                    start_button = gr.Button(
                        value="Start Oobabot",
                        interactive=has_token and not is_running,
                    )
                    stop_button = gr.Button(
                        value="Stop Oobabot",
                        interactive=has_token and is_running,
                    )
                gr.Markdown("### Oobabot Status", elem_id="oobabot-status-heading")
                with gr.Row():
                    log_output = gr.HTML(
                        label="Oobabot Log",
                        value=SAMPLE_HTML,
                        elem_classes=["oobabot-output"],
                    )

    stop_button.click(lambda: oobabot_worker_thread.stop(), [], stop_button)
    start_button.click(lambda: oobabot_worker_thread.start(), [], start_button)


# 1160px
LOG_CSS = """
#discord_bot_token_accordion {
    padding-left: 30px;
}
#oobabot-tab {
}
#oobabot-status-heading {
padding-top: 6px;
}
#oobabot-save-token {
flex:none;
min-width: 50px;
}
#oobabot-refresh-character-menu {
flex:none;
min-width: 50px;
}
#oobabot-tab .prose *{
font-size: 16px;
}
#oobabot-tab .prose h1 {
font-size: 24px;
}
#oobabot-tab .prose h2 {
padding-top: 20px;
font-size: 18px;
}
#oobabot-tab .oobabot_instructions code {
    font-size: 18px;
}
#oobabot-tab .oobabot_instructions h1 code {
    font-size: 24px;
}
#oobabot-tab div.oobabot-output {
    background-color: #0C0C0C;
    color: #CCCCCC;
    font-family: Consolas, Lucida Console, monospace;
    padding:20px;
    border-radius: var(--block-radius);
    min-height: 1160px;
    width: 100%;
}
#oobabot-tab .prose * {
color: unset;
}
#oobabot-tab .prose * .oobabot-red {
    color: #C50F1F;
}
#oobabot-tab .prose * .oobabot-yellow {
    color: #C19C00;
}
#oobabot-tab .prose * .oobabot-cyan {
    color: #3A96DD;
}
#oobabot-tab .prose * .oobabot-white {
    color: #CCCCCC;
}
"""

SAMPLE_HTML = """

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>oobabot logs</title>
<style>
body {
    background-color: #0C0C0C;
    color: #CCCCCC;
    font-family: Consolas, Lucida Console, monospace;
}
.oobabot-red {
    color: #C50F1F;
}
.oobabot-yellow {
    color: #C19C00;
}
.oobabot-cyan {
    color: #3A96DD;
}
.oobabot-white {
    color: #CCCCCC;
}
</style>
</head>
<body><div class="oobabot-log">
<span class='oobabot-yellow'>2023-05-20 17:34:32,945</span> INFO <span class='oobabot-white'>Oobabooga is at wss://ai.home.rudesoftware.net</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,962</span> INFO <span class='oobabot-white'>Connected to Oobabooga!</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,963</span> INFO <span class='oobabot-white'>Stable Diffusion is at http://selma.home.rudesoftware.net:7861/</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,975</span> DEBUG <span class='oobabot-cyan'>Stable Diffusion: Using default sampler on SD server</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,984</span> DEBUG <span class='oobabot-cyan'>Stable Diffusion: Options are already set correctly, no changes made.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,985</span> DEBUG <span class='oobabot-cyan'>Stable Diffusion: Using negative prompt: animal harm, suicide...</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,985</span> INFO <span class='oobabot-white'>Connected to Stable Diffusion!</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:32,985</span> INFO <span class='oobabot-white'>Connecting to Discord... </span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,603</span> INFO <span class='oobabot-white'>Connected to discord as RosieAI (ID: 1100103511888371712)</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,603</span> DEBUG <span class='oobabot-cyan'>monitoring 25 channels across 1 server(s)</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,603</span> DEBUG <span class='oobabot-cyan'>listening to DMs</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,603</span> DEBUG <span class='oobabot-cyan'>Response Grouping: streamed live into a single message</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>AI name: Rosie</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>AI persona: Here is some background information about Rosie:
 - You are Rosie
 - You are a cat
 - Rosie is a female cat
 - Rosie is owned by Chris, whose nickname is mr_bunny
 - Rosie loves Chris more than anything
 - You are 9 years old
 - You enjoy laying on laps and murder
 - Your personality is both witty and profane
 - The people in this chat room are your friends</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>History: 7 lines </span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>Stop markers: ### End of Transcript ###&lt;|endoftext|&gt;, &lt;|endoftext|&gt;</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>Wakewords: rosie, cat</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>Ooba Client: Splitting responses into messages by English sentence.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>Stable Diffusion: image prompts extracted with regex</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,604</span> DEBUG <span class='oobabot-cyan'>Stable Diffusion: image keywords: draw me, drawing, photo, pic, picture, image, sketch</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:35,605</span> DEBUG <span class='oobabot-cyan'>Registering commands, sometimes this takes a while...</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: lobotomize: Erase Rosie&#x27;s memory of any message before now in this channel.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,477</span> DEBUG <span class='oobabot-cyan'>/logs called by user &#x27;mr_bunny&#x27; in channel #1100109201071681587</span></div></body></html>"""
