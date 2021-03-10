from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, Callable, Optional

from jsgf import RootGrammar, PublicRule, Literal

from r7assistant.microphone import Microphone
from r7assistant.recognizer import Recognizer

Action = Callable[['Assistant'], None]


@dataclass
class Skill:
    command: str
    action: Action


class SkillCollection:
    def __init__(self):
        self.skills: Dict[str, Skill] = dict()

    def add(self, name: str, command: str, action: Action) -> None:
        self.skills[name] = Skill(command, action)

    def build_jsgf(self) -> str:
        return RootGrammar(PublicRule(name, Literal(skill.command)) for name, skill in self.skills.items()).compile()

    def find_by_command(self, command: str) -> Skill:
        for skill in self.skills.values():
            if skill.command == command:
                return skill
        raise KeyError


class Assistant:
    def __init__(self, name: str, name_threshold: int):
        self.name = name
        self.name_threshold = name_threshold
        self.skills = SkillCollection()
        self.microphone: Optional[Microphone] = None

    @contextmanager
    def mute_microphone(self):
        if self.microphone is not None:
            self.microphone.muted = True
            yield
            self.microphone.muted = False
        else:
            yield

    def add_skill(self, command: str):
        def decorator(func):
            self.skills.add(func.__name__, f'{self.name} {command}', func)
            return func

        return decorator

    def resolve(self, command: str) -> Skill:
        return self.skills.find_by_command(command)


def run_assistant(assistant: Assistant,
                  hmm_file: Path,
                  dict_file: Path):
    # Load keywords and grammar
    current_dir = Path.cwd()

    grammar = current_dir / 'assistant-grammar.jsgf'
    with open(grammar, 'w') as f:
        f.write(assistant.skills.build_jsgf())

    keywords = current_dir / 'assistant-keywords.list'
    with open(keywords, 'w') as f:
        f.write(f'{assistant.name} /1e{assistant.name_threshold}/\n')

    # Create recognizer
    recognizer = Recognizer(hmm_file, dict_file, keywords, grammar)

    # Queue of phrases
    command_queue = Queue()

    # Phrase handler
    def phrase_callback(audio: bytes):
        if recognizer is None:
            return
        if not recognizer.recognize_keywords(audio):
            print('No keywords found')
        else:
            text = recognizer.recognize_grammar(audio)
            if not text:
                print('Not recognized!')
            else:
                print(text)
                command_queue.put(text)

    # Start assistant
    assistant.microphone = Microphone()
    print('Say something')
    with assistant.microphone.record(phrase_callback):
        while True:
            phrase = command_queue.get()
            assistant.resolve(phrase).action(assistant)
