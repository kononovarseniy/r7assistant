from pathlib import Path

import pocketsphinx as ps


class Recognizer:
    SAMPLERATE = 16000
    CHANNELS = 1

    def __init__(self,
                 hmm_file: Path,
                 dict_file: Path,
                 keywords_file: Path,
                 grammar_file: Path):
        assert keywords_file.is_file(), "Keywords file is not found"
        assert grammar_file.is_file(), "Grammar file is not found"

        self.decoder = ps.Pocketsphinx(
            hmm=str(hmm_file),
            dict=str(dict_file)
        )
        self.decoder.set_kws('keywords', str(keywords_file))
        self.decoder.set_jsgf_file('grammar', str(grammar_file))

    def recognize_keywords(self, data: bytes) -> str:
        self.decoder.set_search('keywords')
        with self.decoder.start_utterance():
            self.decoder.process_raw(data, no_search=False, full_utt=True)

        return self.decoder.hypothesis()

    def recognize_grammar(self, data: bytes) -> str:
        self.decoder.set_search('grammar')
        # oleg.decoder.set_search('_default')
        with self.decoder.start_utterance():
            self.decoder.process_raw(data, no_search=False, full_utt=True)

        return self.decoder.hypothesis()
