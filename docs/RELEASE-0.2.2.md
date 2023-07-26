
# Release v.0.2.2

## What's Changed

Quick bug-fix release to accommodate a breaking change which was added into
transformers after v4.27.0, [in this commit](https://github.com/huggingface/transformers/commit/c7f3abc257af9dfb6006a76f2b09b48355322d4d).

This error would prevent models from being loaded when the oobabot-plugin
is installed.

## New UI Features

* None

## UI Bug Fixes

* None

## New Backend Features

* None (this still uses the `oobabot` 0.2.1 backend)

## Bug Fixes / Tech Improvements

* [Issue 24](https://github.com/chrisrude/oobabot-plugin/issues/24): error when loading model with newer version of transformers

### Full Changelog

[All changes from 0.2.1 to 0.2.2: UI](https://github.com/chrisrude/oobabot-plugin/compare/v0.2.1...v0.2.2)
