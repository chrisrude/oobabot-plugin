#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone main for oobabot_plugin
"""

import gradio

from oobabot_plugin import bootstrap


def web_main(_cwd: str) -> None:
    with gradio.Blocks(analytics_enabled=False, title="oobabot") as gradio_server:
        bootstrap.plugin_ui("0", {})

    gradio_server.queue()
    gradio_server.launch(
        server_name="0.0.0.0",
        server_port=1234,
    )
