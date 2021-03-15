import inspect
from dataclasses import dataclass
from typing import List, Callable

from jsgf import Grammar, RootGrammar, PublicRule, Literal

from r7assistant.decoder import Keyword, KeywordList


@dataclass
class ModuleCommand:
    phrase: str
    function: Callable


def command(phrase: str):
    def decorator(func: Callable):
        return ModuleCommand(phrase, func)

    return decorator


class Module:
    __keywords__: KeywordList

    def __init_subclass__(cls, /, phrase_prefix: str = '', **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__commands__: List[ModuleCommand] = []
        for _, member in inspect.getmembers(cls):
            if isinstance(member, ModuleCommand):
                if phrase_prefix:
                    member.phrase = f'{phrase_prefix} {member.phrase}'
                cls.__commands__.append(member)

    @property
    def keywords(self) -> KeywordList:
        return self.__keywords__

    @property
    def commands(self) -> List[ModuleCommand]:
        return self.__commands__

    @property
    def grammar(self) -> Grammar:
        return RootGrammar(PublicRule(f'cmd-{i}', Literal(cmd.phrase)) for i, cmd in enumerate(self.commands))

    def execute_command(self, phrase: str, state) -> bool:
        for cmd in self.commands:
            if cmd.phrase == phrase:
                cmd.function(self, state)
                return True
        return False
