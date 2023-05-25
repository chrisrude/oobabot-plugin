#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone main for oobabot_plugin
"""

import gradio

from oobabot_plugin import bootstrap


def web_main(_cwd: str) -> None:
    gradio_server = gradio.Blocks(
        analytics_enabled=False,
        title="oobabot",
        css=bootstrap.custom_css(),
    )
    with gradio_server:
        bootstrap.plugin_ui()

    gradio_server.queue()
    gradio_server.launch(
        prevent_thread_lock=True,
        server_name="0.0.0.0",
        server_port=1234,
    )
    gradio_server.server.config.timeout_graceful_shutdown = 1
    gradio_server.block_thread()
