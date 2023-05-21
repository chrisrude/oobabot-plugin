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
        self.reload()

    def reload(self) -> None:
        """
        Stops the oobabot if it's running, then reloads it.
        """
        if not self.is_running():
            return

        if self.thread is not None:
            self.bot.stop()
            self.thread.join()
            self.thread = None

        args = [
            "--config",
            os.path.abspath(self.config_file),
            "--base-url",
            f"http://localhost:{self.port}/",
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
