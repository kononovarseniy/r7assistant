from dataclasses import dataclass
from typing import Callable, List, Optional, Any

from jsgf import RootGrammar, PublicRule, Literal

from r7assistant.assistant import Assistant, Recognizer, RecognizerFactory
from r7assistant.decoder import Keyword, KeywordList, Decoder


@dataclass
class CommandInfo:
    phrase: str
    function: Callable


def _call_method(self, func: Optional[Callable]):
    return func(self) if func is not None else None


class SimpleRecognizer(RecognizerFactory):
    def __init__(self, phrase_prefix: str = ''):
        self._phrase_prefix = phrase_prefix
        self._keywords: List[Keyword] = list()
        self._commands: List[CommandInfo] = list()
        self._on_no_keywords: Optional[Callable] = None
        self._on_not_recognized: Optional[Callable] = None

    def command(self, phrase: str):
        def decorator(func: Callable):
            text = f'{self._phrase_prefix} {phrase}' if self._phrase_prefix else phrase
            cmd = CommandInfo(text, func)
            self._commands.append(cmd)
            return cmd

        return decorator

    def keyword(self, word: str, threshold: int) -> None:
        self._keywords.append(Keyword(word, threshold))

    def on_no_keywords(self, func):
        self._on_no_keywords = func

    def on_not_recognized(self, func):
        self._on_not_recognized = func

    def create(self, module_name: str, module: Any):
        commands = list(self._commands)
        grammar = RootGrammar(PublicRule(f'cmd-{i}', Literal(cmd.phrase)) for i, cmd in enumerate(commands))
        keywords = KeywordList(self._keywords)
        on_no_keywords = self._on_no_keywords
        on_not_recognized = self._on_not_recognized

        class Instance(Recognizer):
            def register(self, decoder: Decoder):
                decoder.register_keywords(module_name, keywords)
                decoder.register_grammar(module_name, grammar)

            def recognize(self, state: Assistant, audio: bytes):
                decoder = state.decoder
                if not decoder.decode_keywords(module_name, audio):
                    if on_no_keywords is not None:
                        on_no_keywords(module, state)
                else:
                    phrase = decoder.decode_grammar(module_name, audio)
                    if not phrase:
                        if on_not_recognized is not None:
                            on_not_recognized(module, state)
                    else:
                        for cmd in commands:
                            if cmd.phrase == phrase:
                                cmd.function(self, state)
                                return True
                        return False

        return Instance()
