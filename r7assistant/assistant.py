import collections
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from typing import Dict, Optional, Type, Deque

from r7assistant.microphone import Microphone
from r7assistant.module import Module
from r7assistant.recognizer import Recognizer


class RecognitionError(Exception):
    pass


class NoKeywordError(RecognitionError):
    pass


class Assistant:
    def __init__(self, tmp_dir: Path, recognizer: Recognizer):
        self.recognizer = recognizer
        self.microphone: Optional[Microphone] = None
        self._module_stack: Deque[Module] = collections.deque()
        self._loaded_modules: Dict[Type[Module], str] = dict()

        self.tmp_dir = tmp_dir

    @property
    def active_module(self) -> Module:
        return self._module_stack[-1]

    def push_active_module(self, value: Module):
        module_type = type(value)
        # Load module
        if module_type not in self._loaded_modules:
            name = f'module-{len(self._loaded_modules)}'
            self.recognizer.add_mode(name, value.keywords, value.commands, self.tmp_dir)
            self._loaded_modules[module_type] = name

        self._module_stack.append(value)

    def pop_active_module(self):
        self._module_stack.pop()

    def recognize(self, audio: bytes) -> str:
        mode = self._loaded_modules[type(self.active_module)]
        if not self.recognizer.recognize_keywords(mode, audio):
            raise NoKeywordError
        else:
            text = self.recognizer.recognize_grammar(mode, audio)
            if not text:
                raise RecognitionError
            else:
                return text

    @contextmanager
    def mute_microphone(self):
        if self.microphone is not None:
            self.microphone.muted = True
            yield
            self.microphone.muted = False
        else:
            yield


def run_assistant(hmm_file: Path,
                  dict_file: Path,
                  default_module: Module):
    tmp_dir = Path.cwd() / 'tmp'
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Create recognizer
    recognizer = Recognizer(hmm_file, dict_file)
    microphone = Microphone()

    # Start assistant
    assistant = Assistant(tmp_dir, recognizer)
    assistant.microphone = microphone
    assistant.push_active_module(default_module)

    phrase_queue = Queue()
    with microphone.record(phrase_queue.put):
        print('Say something')
        while True:
            audio = phrase_queue.get()
            try:
                print('Processing phrase')
                phrase = assistant.recognize(audio)
                print('<<<', phrase)
                assistant.active_module.execute_command(phrase, assistant)
            except NoKeywordError:
                print('No keywords!')
            except RecognitionError:
                print('Not recognized')
