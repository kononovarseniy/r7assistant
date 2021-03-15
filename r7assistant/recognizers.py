from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Callable, List, Optional, Any

from jsgf import RootGrammar, PublicRule, Literal

from r7assistant.assistant import Assistant, Recognizer, RecognizerFactory, Module
from r7assistant.decoder import Keyword, KeywordList, Decoder


@dataclass
class CommandInfo:
    phrase: str
    function: Callable


class BaseRecognizer(Recognizer, ABC):
    def __init__(self, module_name: str, module: Module):
        self.module_name = module_name
        self.module = module


class KeywordRecognizer(BaseRecognizer):
    def __init__(self, module_name: str, module: Module, keywords: KeywordList, on_no_keywords: Callable):
        super().__init__(module_name, module)
        self.keywords = keywords
        self.on_no_keywords = on_no_keywords

    def register(self, decoder: Decoder):
        decoder.register_keywords(self.module_name, self.keywords)

    def recognize(self, state: Assistant, audio: bytes):
        decoder = state.decoder
        if not decoder.decode_keywords(self.module_name, audio):
            if self.on_no_keywords is not None:
                self.on_no_keywords(self.module, state)
        else:
            self.recognize_matched(state, audio)

    @abstractmethod
    def recognize_matched(self, state: Assistant, audio: bytes):
        pass


class KeywordRecognizerFactory(RecognizerFactory):

    def __init__(self):
        self._keywords: List[Keyword] = list()
        self._on_no_keywords: Optional[Callable] = None

    def keyword(self, word: str, threshold: int) -> None:
        self._keywords.append(Keyword(word, threshold))

    def no_keywords(self, value):
        self._on_no_keywords = value
        return self._on_no_keywords

    @property
    def on_no_keywords(self):
        return self._on_no_keywords

    @property
    def keyword_list(self) -> KeywordList:
        return KeywordList(self._keywords)

    def create(self, module_name: str, module: Any) -> Recognizer:
        return KeywordRecognizer(module_name, module, self.keyword_list, self.on_no_keywords)


class SimpleRecognizer(KeywordRecognizer):
    def __init__(self, module_name: str, module: Module,
                 commands: List[CommandInfo], keywords: KeywordList,
                 on_no_keywords: Callable, on_not_recognized: Callable):
        super().__init__(module_name, module, keywords, on_no_keywords)
        self.commands = commands
        self.on_not_recognized = on_not_recognized

    def register(self, decoder: Decoder):
        super().register(decoder)
        grammar = RootGrammar(PublicRule(f'cmd-{i}', Literal(cmd.phrase)) for i, cmd in enumerate(self.commands))
        decoder.register_grammar(self.module_name, grammar)

    def recognize_matched(self, state: Assistant, audio: bytes):
        decoder = state.decoder
        phrase = decoder.decode_grammar(self.module_name, audio)
        if not phrase:
            if self.on_not_recognized is not None:
                self.on_not_recognized(self.module, state)
        else:
            for cmd in self.commands:
                if cmd.phrase == phrase:
                    cmd.function(self, state)


class SimpleRecognizerFactory(KeywordRecognizerFactory):
    def __init__(self, phrase_prefix: str = ''):
        super().__init__()
        self._phrase_prefix = phrase_prefix
        self._commands: List[CommandInfo] = list()
        self._on_not_recognized: Optional[Callable] = None

    def command(self, phrase: str):
        def decorator(func: Callable):
            text = f'{self._phrase_prefix} {phrase}' if self._phrase_prefix else phrase
            cmd = CommandInfo(text, func)
            self._commands.append(cmd)
            return cmd

        return decorator

    def not_recognized(self, func):
        self._on_not_recognized = func

    @property
    def on_not_recognized(self):
        return self._on_not_recognized

    def create(self, module_name: str, module: Any):
        return SimpleRecognizer(module_name, module,
                                list(self._commands), self.keyword_list,
                                self.on_no_keywords,
                                self.on_not_recognized)
