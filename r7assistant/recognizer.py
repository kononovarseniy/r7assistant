from pathlib import Path
from typing import List

import pocketsphinx as ps
from jsgf import RootGrammar, PublicRule, Literal

from r7assistant.module import Keyword, ModuleCommand


def build_grammar(commands: List[ModuleCommand]) -> str:
    return RootGrammar(PublicRule(f'cmd-{i}', Literal(cmd.phrase)) for i, cmd in enumerate(commands)).compile()


def build_keywords(keywords: List[Keyword]) -> str:
    return '\n'.join(f'{k.keyword} /1e{k.threshold}/' for k in keywords)


class Recognizer:
    SAMPLERATE = 16000
    CHANNELS = 1

    def __init__(self,
                 hmm_file: Path,
                 dict_file: Path):
        self.decoder = ps.Pocketsphinx(
            hmm=str(hmm_file),
            dict=str(dict_file)
        )

    def add_mode(self, mode: str, keywords: List[Keyword], commands: List[ModuleCommand], tmp_dir: Path):
        grammar_file = tmp_dir / f'{mode}-grammar.jsgf'
        with open(grammar_file, 'w') as f:
            f.write(build_grammar(commands))

        keywords_file = tmp_dir / f'{mode}-keywords.list'
        with open(keywords_file, 'w') as f:
            f.write(build_keywords(keywords))

        self.decoder.set_kws(f'{mode}-keywords', str(keywords_file))
        self.decoder.set_jsgf_file(f'{mode}-grammar', str(grammar_file))

    def recognize_keywords(self, mode: str, data: bytes) -> str:
        self.decoder.set_search(f'{mode}-keywords')
        with self.decoder.start_utterance():
            self.decoder.process_raw(data, no_search=False, full_utt=True)

        return self.decoder.hypothesis()

    def recognize_grammar(self, mode: str, data: bytes) -> str:
        self.decoder.set_search(f'{mode}-grammar')
        # oleg.decoder.set_search('_default')
        with self.decoder.start_utterance():
            self.decoder.process_raw(data, no_search=False, full_utt=True)

        return self.decoder.hypothesis()
