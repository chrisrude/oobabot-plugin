# -*- coding: utf-8 -*-
"""
Controller for the oobabot UI plugin.  Contains
all behavior for the UI, but no UI components.
"""

import gradio as gr

from oobabot_plugin import layout
from oobabot_plugin import strings
from oobabot_plugin import worker

# todo: params text box for the stable diffusion settings


class OobabotController:
    """
    Controller for the oobabot UI plugin.  Contains
    all behavior for the UI, but no UI components
    or state.
    """

    is_using_character: bool

    def __init__(
        self,
        port: int,
        config_file: str,
        api_extension_loaded: bool,
    ):
        self.layout = layout.OobabotLayout()
        self.worker = worker.OobabotWorker(port, config_file, self.layout)
        self.api_extension_loaded = api_extension_loaded
        self.is_using_character = False

    def _init_button_enablers(
        self,
        token: str,
        plausible_token: bool,
    ) -> None:
        """
        Sets up handlers which will enable or disable buttons
        based on the state of other inputs.
        """

        # first, set up the initial state of the buttons, when the UI first loads
        def enable_when_token_plausible(component: gr.components.IOComponent) -> None:
            component.attach_load_event(
                lambda: component.update(interactive=plausible_token),
                None,
            )

        enable_when_token_plausible(self.layout.discord_token_save_button)
        enable_when_token_plausible(self.layout.ive_done_all_this_button)
        enable_when_token_plausible(self.layout.start_button)

        # initialize the discord invite link value
        self.layout.discord_invite_link_html.attach_load_event(
            lambda: self.layout.discord_invite_link_html.update(
                # pretend that the token is valid here if it's plausible,
                # but don't show a green check
                value=strings.update_discord_invite_link(
                    token,
                    plausible_token,
                    False,
                    self.worker.bot.generate_invite_url,
                )
            ),
            None,
        )

        # turn on a handler for the token textbox which will enable
        # the save button only when the entered token looks plausible
        self.layout.discord_token_textbox.change(
            lambda token: self.layout.discord_token_save_button.update(
                interactive=strings.token_is_plausible(token)
            ),
            inputs=[self.layout.discord_token_textbox],
            outputs=[
                self.layout.discord_token_save_button,
            ],
        )

    def _get_input_handlers(self):
        return self.worker.get_input_handlers(strings.get_available_characters)

    def _init_button_handlers(self) -> None:
        """
        Sets handlers that are called when buttons are pressed
        """

        def handle_save_click(*args):
            # we've been passed the value of every input component,
            # so pass each in turn to our input handler

            results = []

            # iterate over args and input_handlers in parallel
            for new_value, handler in zip(args, self._get_input_handlers().values()):
                update = handler.update_component_from_event(new_value)
                results.append(update)

            self.worker.save_settings()

            return tuple(results)

        def handle_save_discord_token(*args):
            # we've been passed the value of every input component,
            # so pass each in turn to our input handler

            # result is a tuple, convert it to a list so we can modify it
            results = list(handle_save_click(*args))

            # get the token from the settings
            token = self.worker.bot.settings.discord_settings.get_str("discord_token")
            is_token_valid = self.worker.bot.test_discord_token(token)

            # results has most of our updates, but we also need to provide ones
            # for the discord invite link and the "I've done all this" button
            results.append(
                self.layout.discord_invite_link_html.update(
                    value=strings.update_discord_invite_link(
                        token,
                        is_token_valid=is_token_valid,
                        is_tested=True,
                        fn_generate_invite_url=self.worker.bot.generate_invite_url,
                    )
                )
            )
            results.append(
                self.layout.ive_done_all_this_button.update(interactive=is_token_valid)
            )
            results.append(self.layout.start_button.update(interactive=is_token_valid))

            return tuple(results)

        self.layout.discord_token_save_button.click(
            handle_save_discord_token,
            inputs=[*self._get_input_handlers().keys()],
            outputs=[
                *self._get_input_handlers().keys(),
                self.layout.discord_invite_link_html,
                self.layout.ive_done_all_this_button,
                self.layout.start_button,
            ],
        )

        self.layout.save_settings_button.click(
            handle_save_click,
            inputs=[*self._get_input_handlers().keys()],
            outputs=[*self._get_input_handlers().keys()],
        )

        def handle_character_change(
            character: str,
            ai_name: str,
            persona: str,
            wakewords: str,
        ):
            now_using_character = False
            if character is not None:
                character = character.strip()
                if character and character != strings.CHARACTER_NONE:
                    now_using_character = True

            # wakewords are awkward because they're a shared
            # field between persona and character modes.  So
            # what we do is:
            #  - when switching from character to persona, we
            #    save the wakewords from the character mode
            #    into the settings...
            #      - we then empty out the wakewords field,
            #        and let the persona mode fill it in
            #        with the character's name
            #  - when switching from persona to character, we
            #    reload the wakewords from the settings and
            #    discard whatever the persona mode had put in,
            #    even if it had been changed by the user.
            #    Not the best but might be ok.

            # detect a persona -> character switch
            if not self.is_using_character and now_using_character:
                # this what is in the settings.yml, not
                # the previous selection, but should be ok
                # save textbox to settings
                if wakewords is not None:
                    wakewords = wakewords.strip()
                if wakewords:
                    self._get_input_handlers()[
                        self.layout.wake_words_textbox
                    ].write_to_settings(wakewords)

            # detect a character -> persona switch
            if now_using_character:
                # we still want to clear wakewords
                wakewords = ""
            else:
                # load textbox from settings
                wakewords = self._get_input_handlers()[
                    self.layout.wake_words_textbox
                ].read_from_settings()

            new_ai_name, new_persona, new_wakewords = self.worker.preview_persona(
                character,
                ai_name,
                persona,
                wakewords,
            )
            self.is_using_character = now_using_character

            # no matter what, create a Persona object and feed the
            # settings into it, then display what we get
            # show the AI name and persona text boxes if a character is selected
            return (
                self.layout.ai_name_textbox.update(
                    visible=not now_using_character,
                ),
                self.layout.ai_name_textbox_character.update(
                    value=new_ai_name if now_using_character else "",
                    visible=now_using_character,
                ),
                self.layout.persona_textbox.update(
                    visible=not now_using_character,
                ),
                self.layout.persona_textbox_character.update(
                    value=new_persona if now_using_character else "",
                    visible=now_using_character,
                ),
                self.layout.wake_words_textbox.update(value=new_wakewords),
            )

        self.layout.character_dropdown.change(
            handle_character_change,
            inputs=[
                self.layout.character_dropdown,
                self.layout.ai_name_textbox,
                self.layout.persona_textbox,
                self.layout.wake_words_textbox,
            ],
            outputs=[
                self.layout.ai_name_textbox,
                self.layout.ai_name_textbox_character,
                self.layout.persona_textbox,
                self.layout.persona_textbox_character,
                self.layout.wake_words_textbox,
            ],
        )

        def handle_start(*args):
            # things to do!
            # 1. save settings
            # 2. disable all the inputs
            # 3. disable the start button
            # 4. enable the stop button
            # 5. start the bot
            results = list(handle_save_click(*args))
            # the previous handler will have updated the input's values, but we also
            # want to disable them.  We can do this by merging the dicts.
            for update_dict, handler in zip(
                results, self._get_input_handlers().values()
            ):
                update_dict.update(handler.disabled())

            # we also need to disable the start button, and enable the stop button
            results.append(self.layout.start_button.update(interactive=False))
            results.append(self.layout.stop_button.update(interactive=True))

            # now start the bot!
            self.worker.start()

            return list(results)

        # start button!!!!
        self.layout.start_button.click(
            handle_start,
            inputs=[
                *self._get_input_handlers().keys(),
                self.layout.start_button,
                self.layout.stop_button,
            ],
            outputs=[
                *self._get_input_handlers().keys(),
                self.layout.start_button,
                self.layout.stop_button,
            ],
        )

        def handle_stop():
            # things to do!
            # 1. stop the bot
            # 2. enable all the inputs
            # 3. enable the start button
            # 4. disable the stop button
            self.worker.reload()

            results = []
            for handler in self._get_input_handlers().values():
                results.append(handler.enabled())

            results.append(self.layout.start_button.update(interactive=True))
            results.append(self.layout.stop_button.update(interactive=False))

            return tuple(results)

        # stop button!!!!
        self.layout.stop_button.click(
            handle_stop,
            inputs=[],
            outputs=[
                *self._get_input_handlers().keys(),
                self.layout.start_button,
                self.layout.stop_button,
            ],
        )

    ##################################
    # oobabooga <> extension interface

    def init_ui(self) -> None:
        """
        Creates custom gradio elements when the UI is launched.
        """

        token = self.worker.bot.settings.discord_settings.get_str("discord_token")
        plausible_token = strings.token_is_plausible(token)
        image_words = self.worker.bot.settings.stable_diffusion_settings.get_list(
            "image_words"
        )
        stable_diffusion_keywords = [str(x) for x in image_words]

        self.is_using_character = self.worker.is_using_character(
            strings.get_available_characters,
        )

        self.layout.layout_ui(
            get_logs=self.worker.get_logs,
            has_plausible_token=plausible_token,
            stable_diffusion_keywords=stable_diffusion_keywords,
            api_extension_loaded=self.api_extension_loaded,
            is_using_character=self.is_using_character,
        )

        # create our own handlers for every input event which will map
        # between our settings object and its corresponding UI component

        # for all input components, add initialization handlers to
        # set their values from what we read from the settings file
        for component_to_setting in self._get_input_handlers().values():
            component_to_setting.init_component_from_setting()

        # sets up what happens when each button is pressed
        self._init_button_handlers()

        # enables or disables buttons based on the state of other inputs
        self._init_button_enablers(token, plausible_token)
