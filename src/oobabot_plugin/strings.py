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

# the discord token has this format:
# AAAAAAAAAAAAAAAAAAAAAAAAAA.BBBBBB.CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
#
# where each section, A, B, and C, is independently a base64-encoded string.
#
# Section A encodes the Client ID.
#
# The client ID is a "snowflake", which is inherently a 64-bit integer value.
# Before being stored, this value is converted to a decimal string representation,
# then that string is encoded with base64.
#
#   Its structure:
#
#  bits            (42)                        (5)   (5)     (12)
#  ddddddddddddddddddddddddddddddddddddddddd ccccc bbbbb aaaaaaaaaaaaa
#          100101100100111111100000000100101 00000 00000 000000000000
# where:
#   d - number of milliseconds since the Discord epoch (2015-01-01T00:00:00.000Z)
#   c - client ID
#   b - process ID
#   a - incrementing counter (per process)
#
# Discord was only created in May 2015, and the lowest known snowflake (belonging
# to the Discord CTO) is '21154535154122752', it having been generated on Friday
# February 27, 2015 at 09:13:41.112 UTC.
#
# When put into an entire snowflake, this has an encoded length of 24 characters.
#
# The very last token ever, generated sometime in the UTC afternoon of May 13, 2154,
# could have an encoded length of 28 characters.
#
# Due to the way that base64 encoding works, the length of the encoded string would
# normally always be a multiple of 4.  However, after the encoding is done, Discord
# drops the trailing '=' characters, which means that the length of the encoded
# string is not always a multiple of 4.
#
# So, valid lengths for section A are: 24, 25, 26, 27, and 28.
#
# Adding in the other 46 characters (from the two period separators, fixed-length
# sections B and C of 6 and 38 characters, respectively), we get the valid lengths
# for the entire token:
#   70, 71, 72, 73, 74
#
TOKEN_LEN_VALID_RANGE = range(70, 74 + 1)

QUICK_UPDATE_INTERVAL_SECONDS: float = 0.5


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


def get_transcript_markdown() -> str:
    return resource("transcript.md")


def get_css() -> str:
    return resource("oobabot_log.css")


def get_js() -> str:
    return resource("oobabot_log.js")


def token_is_plausible(token: str) -> bool:
    return len(token.strip()) in TOKEN_LEN_VALID_RANGE


def format_save_result(yaml_error: typing.Optional[str]) -> str:
    if yaml_error:
        return "❌ **Error**: " + yaml_error
    return "✔️ **Saved**"


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


CHARACTER_NONE = "None"


def get_available_characters() -> typing.List[str]:
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
    characters.insert(0, CHARACTER_NONE)
    return characters


OTHER_HACKED_LOGGING_ATTRIBUTES = [
    "warning_advice",
    "warning_once",
]


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
    saved_hacked_attributes = {}
    for attr in OTHER_HACKED_LOGGING_ATTRIBUTES:
        if hasattr(logging.Logger, attr):
            saved_hacked_attributes[attr] = getattr(logging.Logger, attr)

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
    # restore other hacked-on attributes
    for attr, value in saved_hacked_attributes.items():
        setattr(logging.Logger, attr, value)

    return ooba_logger


STATUS_PREFIX = "<h3>Oobabot Status</h3>"


def status_heading(status: str) -> str:
    if status == "running":
        return (
            STATUS_PREFIX
            + '<div class="oobabot_status oobabot_status_running">Running</div>'
        )
    if status == "stopped":
        return (
            STATUS_PREFIX
            + '<div class="oobabot_status oobabot_status_stopped">Stopped</div>'
        )
    return STATUS_PREFIX
