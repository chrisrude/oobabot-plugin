import os
import threading

from oobabot import oobabot


class OobabotWorker:
    """
    This class is responsible for running oobabot in a worker thread.
    """

    def __init__(self, port: int, config_file: str):
        """
        port: The port the streaming API is running on
        """
        self.config_file = config_file
        self.port = port
        self.thread = None
        self.stopping = False
        self.reload()

    def reload(self) -> None:
        """
        Stops oobabot if it's running, then reloads it.
        """
        if self.thread is not None:
            self.stopping = True
            self.bot.stop()
            self.thread.join()
            self.stopping = False
            self.thread = None

        args = [
            "--config",
            os.path.abspath(self.config_file),
            "--base-url",
            f"ws://localhost:{self.port}/",
        ]
        self.bot = oobabot.Oobabot(args)

    def start(self) -> None:
        """
        Stops the oobabot if it's running, then starts it.
        """
        self.reload()
        self.thread = threading.Thread(target=self.bot.start)
        self.thread.start()

    def is_running(self) -> bool:
        """
        Returns True if oobabot is running.
        This does not mean that it is connected to discord,
        only that its main loop is running.
        """
        return self.thread is not None and self.thread.is_alive()

    def has_discord_token(self) -> bool:
        """
        Returns True if the user has entered a discord token.
        """
        if self.bot.settings.discord_settings.get_str("discord_token"):
            return True
        return False

    def get_logs(self) -> str:
        """
        Returns the logs from the oobabot.
        """
        if self.bot is None:
            return ""

        lines = oobabot.fancy_logger.recent_logs.get_all()
        return (
            '<div class="oobabot-log">' + "\n<br>".join(lines) + "</div></body></html>"
        )
