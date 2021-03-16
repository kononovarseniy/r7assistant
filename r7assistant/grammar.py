from abc import abstractmethod, ABC
from typing import Union, List, Iterable

import jsgf.expansions as jsgf
import pyparsing


class Expression:
    @abstractmethod
    def to_jsgf(self) -> jsgf.Expansion:
        pass

    @abstractmethod
    def to_parser(self):
        pass


def _expression_sequence(items: Iterable[Union[str, Expression]]) -> List[Expression]:
    res = []
    for i in items:
        if isinstance(i, str):
            res.extend(map(Word, i.split()))
        elif isinstance(i, Expression):
            res.append(i)

    return res


def add_action(expr, action):
    if action is None:
        return expr
    else:
        return expr.addParseAction(action)


class Word(Expression):
    def __init__(self, word: str, *, action=None):
        assert word.isalpha()
        self._word = word.lower()
        self._action = action

    def to_jsgf(self):
        return jsgf.Literal(self._word)

    def to_parser(self):
        return add_action(pyparsing.Keyword(self._word), self._action)


class BaseExpression(Expression, ABC):
    def __init__(self, *items: Union[str, Expression], action=None):
        self._action = action
        self._items = _expression_sequence(items)

    @property
    def action(self):
        return self._action

    @property
    def jsgf_items(self):
        return [i.to_jsgf() for i in self._items]

    @property
    def jsgf_and(self):
        return jsgf.Sequence(*self.jsgf_items)

    @property
    def parsing_items(self):
        return [i.to_parser() for i in self._items]

    @property
    def parsing_and(self):
        return pyparsing.And(self.parsing_items)


class And(BaseExpression):
    def to_jsgf(self):
        return self.jsgf_and

    def to_parser(self):
        return add_action(self.parsing_and, self.action)


class Or(BaseExpression):
    def to_jsgf(self):
        return jsgf.AlternativeSet(*self.jsgf_items)

    def to_parser(self):
        return add_action(pyparsing.Or(self.parsing_items), self.action)


class Suppress(BaseExpression):
    def to_jsgf(self):
        return self.jsgf_and

    def to_parser(self):
        return add_action(pyparsing.Suppress(self.parsing_and), self.action)


class ZeroOrMore(And):
    def to_jsgf(self):
        return jsgf.KleeneStar(self.jsgf_and)

    def to_parser(self):
        return add_action(pyparsing.ZeroOrMore(self.parsing_and), self.action)


class OneOrMore(And):
    def to_jsgf(self):
        return jsgf.Repeat(self.jsgf_and)

    def to_parser(self):
        return add_action(pyparsing.OneOrMore(self.parsing_and), self.action)
