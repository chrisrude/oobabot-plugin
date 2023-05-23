# -*- coding: utf-8 -*-
"""
Stores constant values to display in the UI.

Including:
 - instructional markdown
 - custom css
 - custom js
"""


import typing

TOKEN_LEN_CHARS = 72


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


INSTRUCTIONS_PART_1_MD = """
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
#oobabot-tab .prose #oobabot-invite-link pre {
    display:inline;
    color: orange;
    text-decoration: underline;
}
#oobabot-refresh-character-menu {
flex:none;
min-width: 50px;
}
#oobabot-tab .prose *{
font-size: 16px;
}
#oobabot-tab .prose h1 {
padding-top: 10px;
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

CUSTOM_JS = """
var done_all_this = document.getElementById("oobabot_done_all_this");
console.log(done_all_this);
done_all_this.addEventListener(
    "click",
    function() {
        var elem = document.querySelector("#discord_bot_token_accordion > .open");
        elem.click();
    }
);
"""
