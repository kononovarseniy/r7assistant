from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

import pocketsphinx as ps
from jsgf import Grammar


def _make_grammar_name(name: str) -> str:
    return f'{name}-grammar'


def _make_grammar_filename(name: str) -> str:
    return f'{name}-grammar.jsgf'


def _make_keywords_name(name: str) -> str:
    return f'{name}-keywords'


def _make_keywords_filename(name: str) -> str:
    return f'{name}-keywords.list'


@dataclass
class Keyword:
    keyword: str
    threshold: int


class KeywordList(List[Keyword]):
    def compile(self) -> str:
        return '\n'.join(f'{k.keyword} /1e{k.threshold}/' for k in self)


class Decoder:
    SAMPLERATE = 16000
    CHANNELS = 1

    def __init__(self,
                 hmm_file: Path,
                 dict_file: Path,
                 tmp_dir: Path):
        self.decoder = ps.Pocketsphinx(
            hmm=str(hmm_file),
            dict=str(dict_file)
        )
        self._tmp_dir = tmp_dir

        self._registered_grammars: Set[str] = set()
        self._registered_keyword_lists: Set[str] = set()

    def register_grammar(self, name: str, grammar: Grammar) -> None:
        if name in self._registered_grammars:
            raise KeyError(f'Grammar with name "{name}" is already registered')
        grammar_file = self._tmp_dir / _make_grammar_filename(name)
        with open(grammar_file, 'w') as f:
            f.write(grammar.compile())

        self.decoder.set_jsgf_file(_make_grammar_name(name), str(grammar_file))

    def register_keywords(self, name: str, keywords: KeywordList) -> None:
        if name in self._registered_keyword_lists:
            raise KeyError(f'Keyword list with name "{name}" is already registered')
        keywords_file = self._tmp_dir / _make_keywords_filename(name)
        with open(keywords_file, 'w') as f:
            f.write(keywords.compile())

        self.decoder.set_kws(_make_keywords_name(name), str(keywords_file))

    def _decode(self, search: str, data: bytes) -> str:
        self.decoder.set_search(search)
        with self.decoder.start_utterance():
            self.decoder.process_raw(data, no_search=False, full_utt=True)
        return self.decoder.hypothesis()

    def decode_keywords(self, mode: str, data: bytes) -> str:
        if mode not in self._registered_keyword_lists:
            raise KeyError(f'Keyword list with name "{mode}" not found')
        return self._decode(_make_keywords_name(mode), data)

    def decode_grammar(self, mode: str, data: bytes) -> str:
        if mode not in self._registered_grammars:
            raise KeyError(f'Grammar with name "{mode}" not found')
        return self._decode(_make_grammar_name(mode), data)
