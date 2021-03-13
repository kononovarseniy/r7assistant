import inspect
from dataclasses import dataclass
from typing import List, Callable


@dataclass
class ModuleCommand:
    phrase: str
    function: Callable


@dataclass
class Keyword:
    keyword: str
    threshold: int


def command(phrase: str):
    def decorator(func: Callable):
        return ModuleCommand(phrase, func)

    return decorator


class Module:
    __keywords__: List[Keyword] = list()

    def __init_subclass__(cls, /, phrase_prefix: str = '', **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__commands__: List[ModuleCommand] = []
        for _, member in inspect.getmembers(cls):
            if isinstance(member, ModuleCommand):
                if phrase_prefix:
                    member.phrase = f'{phrase_prefix} {member.phrase}'
                cls.__commands__.append(member)

    @property
    def commands(self) -> List[ModuleCommand]:
        return self.__commands__

    @property
    def keywords(self) -> List[Keyword]:
        return self.__keywords__

    def execute_command(self, phrase: str, state) -> bool:
        for cmd in self.commands:
            if cmd.phrase == phrase:
                cmd.function(self, state)
                return True
        return False
