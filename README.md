# r7assistant

A set of utilities for creating simple voice assistants

## Example

A simple voice assistant named Oleg. The example requires the festival package to be installed. You also need to load
language data for pocketsphix.

```python
import os
from r7assistant import Assistant, run_assistant, Module, command, Keyword


def say_text(state, text: str):
    print('>>>', text)
    with state.mute_microphone():
        os.system(f"echo '{text}' | festival --tts")


class DefaultMode(Module, phrase_prefix='oleg'):  # Each phrase should start with the _word 'Oleg'
    __keywords__ = [Keyword('oleg', -30)]  # -30 is the keyword recognition threshold

    @command('say hello')
    def say_hello(self, state: Assistant):
        say_text(state, 'Hello')

    @command('silent mode')
    def silent_mode(self, state: Assistant):
        say_text(state, 'Switching to silent mode')
        state.push_active_module(SilentMode())

    @command('Who are you')
    def who_are_you(self, state: Assistant):
        say_text(state, 'I am just Oleg')


class SilentMode(Module):
    __keywords__ = [Keyword('oleg', -10)]

    @command('oleg active mode')
    def active_mode(self, state: Assistant):
        say_text(state, 'Switching to active mode')
        state.pop_active_module()


def main():
    from pathlib import Path

    # Change path to the pocketsphinx language data directory
    lang_dir = Path('PATH TO POCKETSPHINX DATA DIRECTORY').resolve()
    run_assistant(lang_dir / 'PATH TO ACOUSTIC MODEL DIRECTORY',
                  lang_dir / 'PATH TO DICTIONARY FILE.dic',
                  DefaultMode())


if __name__ == '__main__':
    main()
```