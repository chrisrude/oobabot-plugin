# import ctypes
# import multiprocessing

import os
import threading

import gradio as gr
from oobabot import oobabot

import modules

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
# Oobabot
"""


def _init_token_setup():
    # steps
    # on https://discord.com/developers/applications
    #  New Application
    #    enter name and "Create"
    #
    # Bot
    #  turn off "public bot", probably
    # turn on
    #   "Server Members" and "Message Content" intent
    #   "Presence Intent" should be off
    # hit "reset token" > copy token
    # paste token here: MTEwOTY3MTk4NzE0MTQzMTM4OA.G9xxVq.QYonUEnssluf5MxYhqrDVlwoDAZaoPshpVIVhQ
    #
    # first part seems to be base64 encoded client ID
    # client ID 1109671987141431388
    # permissions hash  309237745664
    # https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={permissions}}&scope=bot
    gr.Markdown(INSTRUCTIONS_MD)
    with gr.Row():
        gr.Textbox(
            label="Discord Token",
            value="",
        )
        gr.Button(label="Test Token")


def _init_persona_settings(settings: oobabot.settings.Settings):
    # with gr.Row():
    #     character_menu = gr.Dropdown(
    #         choices=modules.utils.get_available_characters(),
    #         label="Character",
    #         info="Used in chat and chat-instruct modes.",
    #         interactive=True,
    #     )
    #     modules.ui.create_refresh_button(
    #         character_menu,
    #         lambda: None,
    #         lambda: {"choices": modules.utils.get_available_characters()},
    #         "refresh-button",
    #     )

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
        label="Wakewords",
        value=", ".join(settings.persona_settings.get_list("wakewords")),
        info="""
            One or more words that the bot will listen for.
            The bot will listen in all discord channels can
            access for one of these words to be mentioned, then reply
            to any messages it sees with a matching word.
            The bot will always reply to @-mentions and
            direct messages, even if no wakewords are supplied.
            """,
    )


def _init_advanced_settings():
    gr.Radio(
        ["by sentence", "single message", "streaming"],
        label="Split Responses",
        info="How many messages is a response split into?",
        value="by sentence",
    ),
    gr.Slider(
        label="History Lines",
        minimum=1,
        maximum=30,
        value=7,
    )
    gr.CheckboxGroup(
        ["Ignore DMs", "Reply in Thread"],
        label="Behavior",
        info="Where are they from?",
    )


def _init_status():
    gr.Label(label="Status", value="🔴 Not Running")
    gr.Label(
        label="Messages",
        value="34 sent",
        info="Average time to first response in seconds",
    )
    gr.Label(label="Generation Speed", info="Token Generation Speed in tokens/second")


def _init_oobabot_ui(settings: oobabot.settings.Settings) -> None:
    token = settings.discord_settings.get_str("discord_token")
    has_token = token is not None and len(token) > 0
    has_token = True
    with gr.Blocks():
        with gr.Accordion("Welcome! - Bot Token", open=not has_token):
            _init_token_setup()
        with gr.Row():
            with gr.Column():
                _init_persona_settings(settings=settings)
                with gr.Accordion("Advanced", open=False):
                    _init_advanced_settings()
            with gr.Column():
                with gr.Row():
                    _init_status()
                with gr.Row():
                    start = gr.Button(value="Start Oobabot", interactive=True)
                    start.click(lambda: oobabot_worker_thread.start(), [], start)

                    stop = gr.Button(
                        value="Stop Oobabot", interactive=False
                    )  # , interactive=False
                    stop.click(lambda: oobabot_worker_thread.stop(), [], stop)

                with gr.Row():
                    gr.HTML(
                        label="Oobabot Log", value=SAMPLE_HTML, elem_id="oobabot-log"
                    )


LOG_CSS = """
<style>
#oobabot-log div.oobabot-log {
    background-color: #0C0C0C;
    color: #CCCCCC;
    font-family: Consolas, Lucida Console, monospace;
}
.oobabot-log .oobabot-red {
    color: #C50F1F;
    font-family: Consolas, Lucida Console, monospace;
}
.oobabot-log .oobabot-yellow {
    color: #C19C00;
    font-family: Consolas, Lucida Console, monospace;
}
.oobabot-log .oobabot-cyan {
    color: #3A96DD;
    font-family: Consolas, Lucida Console, monospace;
}
.oobabot-log .oobabot-white {
    color: #CCCCCC;
    font-family: Consolas, Lucida Console, monospace;
}
</style>
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
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: logs: Return the most recent log messages from the bot server.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,075</span> INFO <span class='oobabot-white'>Registered command: say: Force Rosie to say the provided message.</span>
<br><span class='oobabot-yellow'>2023-05-20 17:34:36,477</span> DEBUG <span class='oobabot-cyan'>/logs called by user &#x27;mr_bunny&#x27; in channel #1100109201071681587</span></div></body></html>"""
