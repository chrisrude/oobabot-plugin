# -*- coding: utf-8 -*-
"""
Renders a transcript of the current audio conversation.
"""

import datetime
import html
import typing

from oobabot import discrivener
from oobabot import transcript

SEPARATE_MESSAGE_DELTA = datetime.timedelta(seconds=10)


def get_transcript_html(
    get_transcript: typing.Callable[[], typing.Optional[transcript.Transcript]]
) -> str:
    """
    Formats a transcript into a string.
    """
    transcription = get_transcript()

    lines: list[transcript.TranscriptLine]
    if transcription is None:
        lines = []
    else:
        lines = transcription.get_lines()

    user_id_to_user = {}
    for line in lines:
        if line.user is not None and line.original_message is not None:
            user_id_to_user[line.original_message.user_id] = line.user

    user_id_to_header = {}
    for user_id, user in user_id_to_user.items():
        user_id_to_header[user_id] = format_user_header(user)

    user_id_to_header[-1] = format_bot_header()

    # get each original transcription (aka user message) from those lines
    user_messages: typing.Set[discrivener.Transcription] = set(
        line.original_message for line in lines if line.original_message
    )

    message_list: typing.List[
        typing.Tuple[datetime.datetime, int, datetime.datetime, str]
    ] = [format_bot_message(line) for line in lines if line.is_bot]

    for message in user_messages:
        message_list.append(format_message(message))

    # order by timestamp
    message_list.sort(key=lambda x: x[0])

    html = ""

    last_uid = -2
    last_timestamp = datetime.datetime.min
    # todo: get persona for bot
    for timestamp, user_id, end_timestamp, message in message_list:
        new_user = False
        time_since_last_message = timestamp - last_timestamp
        if user_id != last_uid or time_since_last_message > SEPARATE_MESSAGE_DELTA:
            if html != "":
                html += format_user_footer()
            new_user = True

        if new_user:
            html += user_id_to_header[user_id]
            last_uid = user_id

        html += '<div class="oobabot_message">'
        html += message
        html += "</div>\n"

        last_timestamp = end_timestamp

    if len(message_list) > 0:
        html += format_user_footer()

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


def format_token(token: discrivener.TokenWithProbability) -> str:
    token_text = '<div class="oobabot_token_text">'
    token_text += html.escape(token.token_text)
    token_text += "</div>"

    confidence_class = "oobabot_confidence_"
    confidence_class += percentage_to_confidence_range(token.probability)

    # important to have no spaces between the divs
    # or they will show up as spaces in between the tokens
    return f'<div class="oobabot_token {confidence_class}">{token_text}</div>'


def format_bot_header() -> str:
    author_html = ' <div class="oobabot_author">'
    author_html += '<div class="oobabot_author_name">'
    author_html += "Bot"
    author_html += "</div></div>\n"

    return f'<div class="oobabot_bot_message">{author_html}\n'


def format_user_header(user) -> str:
    avatar_url = user.display_avatar.url

    author_html = ' <div class="oobabot_author">'
    author_html += f'<img class="oobabot_author_avatar" src="{avatar_url}" />'
    author_html += '<div class="oobabot_author_name">'
    if user is None:
        author_html += "-Unknown-"
    else:
        author_html += html.escape(user.display_name)
    author_html += "</div></div>\n"

    return f'<div class="oobabot_user_message">{author_html}\n'


def format_user_footer() -> str:
    return "</div>\n"


def format_message(
    message: discrivener.Transcription,
) -> typing.Tuple[datetime.datetime, int, datetime.datetime, str]:
    segment_html = ""
    for segment in message.segments:
        segment_html += ' <div class="oobabot_segment">\n'
        for token in segment.tokens_with_probability:
            segment_html += format_token(token)
        segment_html += " </div>\n"

    return (
        message.timestamp,
        message.user_id,
        message.timestamp + message.audio_duration,
        segment_html,
    )


def format_bot_message(
    line: transcript.TranscriptLine,
) -> typing.Tuple[datetime.datetime, int, datetime.datetime, str]:
    # todo: bot stats?
    # use -1 as the bot's user id
    return (
        line.timestamp,
        -1,
        line.timestamp,
        f'<div="bot_message">{html.escape(line.text)}</div>',
    )
