# Release v.0.2.3

## What's Changed

This update is a small bug-fix release to support changes
that were made in the most recent version of the oobabooga server.

It also updates to the latest version of the oobabot backend, which includes a minor feature to disable unsolicited replies
entirely.  This is useful if you want to use the bot in a high-volume channel.

## UI Bug Fixes

* Downgrade gradio to version 3.33.1

Gradio is the UI library which oobabooga uses.  It would specifically use version 3.33.1 of Gradio.

Version 3.33.1, however, has known security vulnerabilities,
[described here](https://github.com/gradio-app/gradio/security/advisories/GHSA-3qqg-pgqq-3695).  These would affect anyone who
was using a "shared" gradio app.

Because of this, oobabot-plugin would force an upgrade of gradio to 3.34.0, which fixed the security issues.  For a long
time, oobabooga would still work fine with this slightly-updated
version.

However, a somewhat recent change to Oobabooga broke compatibility with the newer version of Gradio.  This means
that with any security-patched version, model loading just
doesn't work, no matter if oobabot is installed or not.

Because this is a total breakage of the oobabooga server, we
have no choice but to revert to the older version of Gradio
until the issue is fixed.

## New Backend Features (from the oobabot 0.2.3 backend)

* Option to disable unsolicited replies entirely

Unsolicited replies are still enabled by default, but you can now disable them entirely by changing this setting in your config.yml:

```yaml
  # If set, the bot will not reply to any messages that do not @-mention it or include a
  # wakeword.  If unsolicited replies are disabled, the unsolicited_channel_cap setting will
  # have no effect.
  #   default: False
  disable_unsolicited_replies: true
```

The objective of this change is to support cases where
unsolicited replies are not desired, such as when the bot is used in a
channel with a high volume of messages.

## Bug Fixes / Tech Improvements

* Preserve newlines when prompting the bot

  In some cases the whitespace in user messages is important.  One case is
described in the [issue 76, reported by @xydreen](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-45c4-8wx5-qw6w).

  When sending a prompt to the bot, we will now preserve any newlines
that the bot itself had generated in the past.

  We will still strip newlines from messages from user-generated messages,
as otherwise they would have the ability to imitate our prompt format.
This would let users so inclined to fool the bot into thinking a
message was sent by another user, or even itself.

### Full Changelog

[All changes from 0.2.2 to 0.2.3: UI](https://github.com/chrisrude/oobabot-plugin/compare/v0.2.2...v0.2.3)
[All changes from 0.2.1 to 0.2.3: Backend](https://github.com/chrisrude/oobabot/compare/v0.2.1...v0.2.3)
