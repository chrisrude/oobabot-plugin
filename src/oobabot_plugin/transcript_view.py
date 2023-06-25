# -*- coding: utf-8 -*-
"""
Renders a transcript of the current audio conversation.
"""

import datetime
import html
import typing

from oobabot import transcript
from oobabot import types

SEPARATE_MESSAGE_DELTA = datetime.timedelta(seconds=1)


def get_transcript_html(
    get_transcript: typing.Callable[[], typing.List["types.VoiceMessage"]],
    get_fancy_author: typing.Callable[[int], typing.Optional["types.FancyAuthor"]],
) -> str:
    """
    Formats a transcript into a string.
    """
    messages = get_transcript()
    if not transcript:
        return ""

    user_id_to_header: typing.Dict[int, str] = {}

    # tuple is: (start_time, user_id, end_time, message_html)
    message_list: typing.List[
        typing.Tuple[datetime.datetime, int, datetime.datetime, str]
    ] = []

    for message in messages:
        # create a header for this user if we don't have one
        if message.user_id not in user_id_to_header:
            fancy_author = get_fancy_author(message.user_id)
            if fancy_author is None:
                user_id_to_header[message.user_id] = format_unknown_user_header(
                    message.user_id,
                    message.is_bot,
                )
            else:
                user_id_to_header[message.user_id] = format_header(
                    fancy_author, message.is_bot
                )
        # add the message itself to our list
        if isinstance(message, types.VoiceMessageWithTokens):
            formatted_message = format_user_message(message)
        else:
            formatted_message = format_bot_message(message)

        message_list.append(
            (
                message.start_time,
                message.user_id,
                message.start_time + message.duration,
                formatted_message,
            )
        )

    # order by timestamp
    message_list.sort(key=lambda x: x[0])

    html = ""

    last_uid = -2
    last_timestamp = datetime.datetime.min

    for timestamp, user_id, end_timestamp, message in message_list:
        new_user = False
        time_since_last_message = timestamp - last_timestamp
        if user_id != last_uid or time_since_last_message > SEPARATE_MESSAGE_DELTA:
            if html != "":
                html += format_footer()
            new_user = True

        if new_user:
            html += user_id_to_header[user_id]
            last_uid = user_id

        html += message

        last_timestamp = end_timestamp

    if len(message_list) > 0:
        html += format_footer()

    return html


CONFIDENCE_RANGES = [
    (95, "great"),
    (75, "good"),
    (50, "ok"),
    (25, "bad"),
    (0, "terrible"),
]


def percentage_to_confidence_range(percentage: int) -> str:
    """
    Converts a percentage to a color.
    """
    for threshold, color in CONFIDENCE_RANGES:
        if percentage >= threshold:
            return color
    return CONFIDENCE_RANGES[-1][1]


def format_token(text: str, p: int) -> str:
    confidence_class = "oobabot_confidence_"
    confidence_class += percentage_to_confidence_range(p)

    # important to have no spaces between the divs
    # or they will show up as spaces in between the tokens
    return f'<div class="oobabot_token {confidence_class}">{html.escape(text)}</div>'


def header_class(is_bot: bool) -> str:
    if is_bot:
        return "oobabot_bot_message"
    else:
        return "oobabot_user_message"


def format_header(fancy_author: "types.FancyAuthor", is_bot: bool) -> str:
    author_html = ' <div class="oobabot_author">'
    author_html += (
        f'<img class="oobabot_author_avatar" src="{fancy_author.author_avatar_url}" />'
    )
    # todo: does accent color work?
    author_html += '<div class="oobabot_author_name">'
    author_html += html.escape(fancy_author.author_name)
    author_html += "</div></div>\n"

    return (
        f'<div class="{header_class(is_bot)}">{author_html}'
        + '<div class="oobabot_tokens">\n'
    )


def format_unknown_user_header(user_id: int, is_bot: bool) -> str:
    author_html = ' <div class="oobabot_author">'
    author_html += '<div class="oobabot_author_name">'
    author_html += f"-user {user_id}-"
    author_html += "</div></div>\n"

    return (
        f'<div class="{header_class(is_bot)}">{author_html}'
        + '<div class="oobabot_tokens">\n'
    )


def format_footer() -> str:
    return "</div></div>\n"


def format_user_message(
    user_message: "types.VoiceMessageWithTokens",
) -> str:
    message_html = ""

    for token_text, p in user_message.tokens_with_confidence:
        message_html += format_token(token_text, p)

    return message_html


def format_bot_message(
    message: "types.VoiceMessage",
) -> str:
    return html.escape(message.text)
