#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""
Utility to install/uninstall the oobabot plugin.
"""

import argparse
import importlib.resources
import os
import shutil
import sys


def ensure_in_oobabooga_dir(cwd: str) -> None:
    if os.path.isdir(cwd + "/extensions"):
        return

    print(
        "This script must be run from the root directory of an oobabooga install.",
        file=sys.stderr,
    )
    sys.exit(1)


def do_install(cwd: str) -> None:
    ensure_in_oobabooga_dir(cwd)

    if not os.path.isdir(cwd + "/extensions/oobabot"):
        os.mkdir(cwd + "/extensions/oobabot")

    with importlib.resources.path("oobabot_plugin", "script.py") as path:
        shutil.copy(path, cwd + "/extensions/oobabot/script.py")

    if not os.path.isfile(cwd + "/extensions/oobabot/script.py"):
        print(
            "Failed to copy script.py to extensions/oobabot/script.py",
            file=sys.stderr,
        )
        sys.exit(1)

    print("oobabot installed!")
    print("Please restart the server and enable the oobabot plugin.")


def do_uninstall(cwd: str) -> None:
    ensure_in_oobabooga_dir(cwd)

    # make the ./extensions/oobabot directory if it doesn't exist
    if not os.path.isdir(cwd + "/extensions/oobabot"):
        print("oobabot is not installed.", file=sys.stderr)
        sys.exit(1)

    # remove the file we copied out of our package from that directory
    os.remove(cwd + "/extensions/oobabot/script.py")

    # check that the file is gone
    if os.path.isfile(cwd + "/extensions/oobabot/script.py"):
        print(
            "Failed to remove script.py from extensions/oobabot/script.py",
            file=sys.stderr,
        )
        sys.exit(1)

    # remove the extensions/oobabot directory if it exists
    if os.path.isdir(cwd + "/extensions/oobabot"):
        os.rmdir(cwd + "/extensions/oobabot")

    # check that the directory is gone
    if os.path.isdir(cwd + "/extensions/oobabot"):
        print(
            "Failed to remove extensions/oobabot directory",
            file=sys.stderr,
        )
        sys.exit(1)

    print("oobabot uninstalled!")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_install = subparsers.add_parser("install")
    parser_install.set_defaults(func=do_install)

    parser_uninstall = subparsers.add_parser("uninstall")
    parser_uninstall.set_defaults(func=do_uninstall)

    args = parser.parse_args()

    cwd = os.getcwd()
    args.func(cwd)


# python main
if __name__ == "__main__":
    main()
