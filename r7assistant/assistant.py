import collections
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, Optional, Type, Deque, Any

from r7assistant.decoder import Decoder
from r7assistant.microphone import Microphone


class Recognizer:
    @abstractmethod
    def register(self, decoder: Decoder):
        pass

    @abstractmethod
    def recognize(self, state: 'Assistant', audio: bytes):
        pass


class RecognizerMeta:
    @abstractmethod
    def init(self, module_name: str, module: Any) -> Recognizer:
        pass


class Module:
    recognizer: RecognizerMeta


@dataclass
class ActiveModuleInfo:
    name: str
    recognizer: Recognizer


class Assistant:
    def __init__(self, decoder: Decoder):
        self.decoder = decoder
        self.microphone: Optional[Microphone] = None
        self._module_stack: Deque[ActiveModuleInfo] = collections.deque()
        self._loaded_modules: Dict[Type[Module], str] = dict()

    @property
    def active_module(self) -> ActiveModuleInfo:
        return self._module_stack[-1]

    def push_active_module(self, module: Module) -> None:
        module_type = type(module)

        if module_type in self._loaded_modules:
            name = self._loaded_modules[module_type]
            recognizer = module.recognizer.init(name, module)
        else:
            name = f'module-{len(self._loaded_modules)}'
            self._loaded_modules[module_type] = name
            recognizer = module.recognizer.init(name, module)
            recognizer.register(self.decoder)

        self._module_stack.append(ActiveModuleInfo(name, recognizer))

    def pop_active_module(self) -> None:
        self._module_stack.pop()

    def recognize(self, audio: bytes) -> None:
        self.active_module.recognizer.recognize(self, audio)

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
    decoder = Decoder(hmm_file, dict_file, tmp_dir)
    microphone = Microphone()

    # Start assistant
    assistant = Assistant(decoder)
    assistant.microphone = microphone
    assistant.push_active_module(default_module)

    phrase_queue = Queue()
    with microphone.record(phrase_queue.put):
        print('Say something')
        while True:
            audio = phrase_queue.get()
            print('Processing phrase')
            assistant.recognize(audio)
