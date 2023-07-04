# -*- coding: utf-8 -*-
"""
Sets handlers -- the functions that are called when buttons are pressed
"""
from oobabot_plugin import layout as oobabot_layout
from oobabot_plugin import strings
from oobabot_plugin import worker as oobabot_worker


class ButtonHandlers:
    """
    Implements handlers for the buttons in the UI.
    """

    def __init__(
        self,
        is_using_character: bool,
        layout: oobabot_layout.OobabotLayout,
        worker: oobabot_worker.OobabotWorker,
    ) -> None:
        # this flag is why we have a class for this
        self.is_using_character = is_using_character
        self.layout = layout
        self.worker = worker

        """
        Sets handlers that are called when buttons are pressed
        """

        layout.discord_token_save_button.click(
            self._handle_save_discord_token,
            inputs=[*self._get_input_handlers().keys()],
            outputs=[
                *self._get_input_handlers().keys(),
                layout.discord_invite_link_html,
                layout.ive_done_all_this_button,
                layout.start_button,
            ],
        )

        layout.save_settings_button.click(
            lambda *args: tuple(self._handle_save_click(*args)),
            inputs=[*self._get_input_handlers().keys()],
            outputs=[*self._get_input_handlers().keys()],
        )

        layout.tab_advanced.select(
            self._handle_advanced_tab,
            inputs=[*self._get_input_handlers().keys()],
            outputs=[
                *self._get_input_handlers().keys(),
                layout.advanced_yaml_editor,
                layout.advanced_save_result,
            ],
        )

        layout.advanced_save_settings_button.click(
            self._handle_advanced_save,
            inputs=[layout.advanced_yaml_editor],
            outputs=[
                *self._get_input_handlers().keys(),
                layout.advanced_save_result,
            ],
        )

        layout.ive_done_all_this_button.click(
            None,
            inputs=[],
            outputs=[],
            _js="() => document.querySelector("
            + '"#discord_bot_token_accordion > .open")?.click()',
        )

        layout.character_dropdown.change(
            self._handle_character_change,
            inputs=[
                layout.character_dropdown,
                layout.ai_name_textbox,
                layout.persona_textbox,
            ],
            outputs=[
                layout.ai_name_textbox,
                layout.ai_name_textbox_character,
                layout.persona_textbox,
                layout.persona_textbox_character,
            ],
        )

        # start button!!!!
        layout.start_button.click(
            self._handle_start,
            inputs=[
                *self._get_input_handlers().keys(),
                layout.start_button,
                layout.stop_button,
            ],
            outputs=[
                *self._get_input_handlers().keys(),
                layout.start_button,
                layout.stop_button,
                layout.advanced_save_settings_button,
                layout.advanced_yaml_editor,
            ],
        )

        # stop button!!!!
        layout.stop_button.click(
            self._handle_stop,
            inputs=[],
            outputs=[
                *self._get_input_handlers().keys(),
                layout.start_button,
                layout.stop_button,
                layout.advanced_save_settings_button,
                layout.advanced_yaml_editor,
            ],
        )

    def _get_input_handlers(self):
        return self.worker.get_input_handlers(strings.get_available_characters)

    def _handle_save_click(self, *args):
        # we've been passed the value of every input component,
        # so pass each in turn to our input handler

        results = []
        # iterate over args and input_handlers in parallel
        for new_value, handler in zip(args, self._get_input_handlers().values()):
            update = handler.update_component_from_event(new_value)
            results.append(update)

        self.worker.save_settings()
        return results

    def _handle_save_discord_token(self, *args):
        # we've been passed the value of every input component,
        # so pass each in turn to our input handler

        # result is a tuple, convert it to a list so we can modify it
        results = self._handle_save_click(*args)

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

    def _handle_advanced_tab(self, *args):
        # when the advanced tab is selected, we need save the
        # settings, then generate the yaml file and display it
        # in the html box
        result = self._handle_save_click(*args)
        result = list(result)

        yaml = self.worker.get_settings_as_yaml()
        result.append(
            self.layout.advanced_yaml_editor.update(
                value=yaml,
            )
        )
        # clear any previous save output, either
        # success or error
        result.append(
            self.layout.advanced_save_result.update(
                value="",
            )
        )
        return tuple(result)

    # handle "Save Settings" on the advanced tab
    def _handle_advanced_save(self, yaml):
        # then, save the yaml to the settings

        save_error = self.worker.set_settings_from_yaml(yaml)

        # finally, update all inputs with the new setting
        # values.  If they haven't changed, these will
        # just be the old values
        results = []

        # iterate over args and input_handlers in parallel
        for component, handler in self._get_input_handlers().items():
            update = component.update(value=handler.read_from_settings())
            results.append(update)

        # finally, write new settings to disk
        self.worker.save_settings()

        results.append(
            self.layout.advanced_save_result.update(
                value=strings.format_save_result(save_error),
            )
        )

        return tuple(results)

    def _handle_character_change(
        self,
        character: str,
        ai_name: str,
        persona: str,
    ):
        now_using_character = False
        if character is not None:
            character = character.strip()
            if character and character != strings.CHARACTER_NONE:
                now_using_character = True

        new_ai_name, new_persona = self.worker.preview_persona(
            character,
            ai_name,
            persona,
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
        )

    def _enable_disable_inputs(self, is_running: bool):
        """
        Enables or disables all the inputs on the page
        based on whether the bot is running or not.

        Maintenance note: this logic is also shadowed in
        the _init_input_enablers() method, so if you update
        this, update that too.
        """
        results = []
        for handler in self._get_input_handlers().values():
            if is_running:
                results.append(handler.disabled())
            else:
                results.append(handler.enabled())

        results.append(self.layout.start_button.update(interactive=not is_running))
        results.append(self.layout.stop_button.update(interactive=is_running))
        results.append(
            self.layout.advanced_save_settings_button.update(interactive=not is_running)
        )
        results.append(
            self.layout.advanced_yaml_editor.update(interactive=not is_running)
        )
        return results

    def _handle_start(self, *args):
        # things to do!
        # 1. save settings
        # 2. disable all the inputs
        # 3. disable the start button
        # 4. enable the stop button
        # 5. disable the advanced save button
        # 6. start the bot

        save_results = self._handle_save_click(*args)
        enable_results = self._enable_disable_inputs(True)

        # the handle_save_click handler will have created updates
        # for the input's values, but we also want to disable them
        # using the dicts from enable_on_running_state.  We can do
        # this by merging the dicts into one.
        for save_result, enable_result in zip(save_results, enable_results):
            save_result.update(enable_result)

        # zip only looks at the keys in common, so move over any
        # keys that are in enable_results but not in save_results
        for update in enable_results[len(save_results) :]:
            save_results.append(update)

        # now start the bot!
        self.worker.start()

        return tuple(save_results)

    def _handle_stop(self):
        # things to do!
        # 1. stop the bot
        # 2. enable all the inputs
        # 3. enable the start button
        # 4. disable the stop button
        # 5. enable the advanced save button
        self.worker.reload()

        results = self._enable_disable_inputs(False)
        return tuple(results)
