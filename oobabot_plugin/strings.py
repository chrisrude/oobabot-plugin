# -*- coding: utf-8 -*-
"""
Stores constant values to display in the UI.

Including:
 - instructional markdown
 - custom css
 - custom js
"""

# import importlib.resources
import importlib
import logging
import os
import pathlib
import sys
import types
import typing

import oobabot.fancy_logger

TOKEN_LEN_CHARS = 72


def resource(name: str) -> str:
    # return importlib.resources.read_text("oobabot_plugin", name)
    return pathlib.Path(os.path.join(os.path.dirname(__file__), name)).read_text(
        encoding="utf-8"
    )


def get_instructions_markdown() -> typing.Tuple[str, str]:
    """
    Returns markdown in two parts, before and after the
    token input box.
    """
    md_text = resource("instructions.md")
    return tuple(md_text.split("{{TOKEN_INPUT_BOX}}", 1))


def get_css() -> str:
    return resource("oobabot_log.css")


def get_js() -> str:
    return resource("oobabot_log.js")


def token_is_plausible(token: str) -> bool:
    return len(token.strip()) >= TOKEN_LEN_CHARS


def make_link_from_token(
    token: str,
    fn_calc_invite_url: typing.Optional[typing.Callable[[str], str]],
) -> str:
    if not token or not fn_calc_invite_url:
        return "A link will appear here once you have set your Discord token."
    link = fn_calc_invite_url(token)
    return (
        f'<a href="{link}" id="oobabot-invite-link" target="_blank">Click here to <pre>'
        + "invite your bot</pre> to a Discord server</a>."
    )


def update_discord_invite_link(
    new_token: str,
    is_token_valid: bool,
    is_tested: bool,
    fn_generate_invite_url: typing.Optional[typing.Callable[[str], str]],
):
    new_token = new_token.strip()
    prefix = ""
    if is_tested:
        if is_token_valid:
            prefix = "✔️ Your token is valid.<br><br>"
        else:
            prefix = "❌ Your token is invalid."
    if is_token_valid:
        return prefix + make_link_from_token(
            new_token,
            fn_generate_invite_url,
        )
    if new_token:
        return prefix
    return "A link will appear here once you have set your Discord token."


def get_available_characters():
    """
    This is a list of all files in the ./characters folder whose
    extension is .json, .yaml, or .yml

    The list is then sorted alphabetically, and 'None' is added to
    the start.
    """
    characters = []
    for extension in ["yml", "yaml", "json"]:
        for filepath in pathlib.Path("characters").glob(f"*.{extension}"):
            characters.append(filepath.stem)
    characters.sort()
    characters.insert(0, "None")
    return characters


def repair_logging() -> typing.Optional[logging.Logger]:
    ##################################
    # so, logging_colors.py, rather than using the logging module's built-in
    # formatter, is monkey-patching the logging module's StreamHandler.emit.
    # This is a problem for us, because we also use the logging module, but
    # don't want ANSI color codes showing up in HTML.  We also don't want
    # to break their logging.
    #
    # So, we're going to save their monkey-patched emit, reload the logging
    # module, save off the "real" emit, then re-apply their monkey-patch.
    #
    # We need to do all this before we create the oobabot_worker, so that
    # the logs created during startup are properly formatted.

    # save the monkey-patched emit
    hacked_emit = logging.StreamHandler.emit

    # reload the logging module
    try:
        importlib.reload(logging)
    except ImportError as err:
        print(f"Oobabot: Error reloading logging module: {err}", file=sys.stderr)
        return None

    # create our logger early
    oobabot.fancy_logger.init_logging(logging.DEBUG, True)
    ooba_logger = oobabot.fancy_logger.get()

    # manually apply the "correct" emit to each of the StreamHandlers
    # that fancy_logger created
    for handler in ooba_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.emit = types.MethodType(logging.StreamHandler.emit, handler)

    logging.StreamHandler.emit = hacked_emit
    return ooba_logger
