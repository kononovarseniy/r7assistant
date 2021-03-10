import audioop
import collections
import math
import sys
from contextlib import contextmanager
from typing import Callable

import sounddevice as sd

from r7assistant.recognizer import Recognizer


class Microphone:
    def __init__(self, energy_threshold: int = 300, speech_threshold: float = 0.3, pause_threshold: float = 0.8):
        self.energy_threshold = energy_threshold
        self.speech_threshold = speech_threshold
        self.pause_threshold = pause_threshold
        self.muted = False

    @contextmanager
    def record(self, callback: Callable[[bytes], None]):
        queue = collections.deque()

        state = 0
        counter = 0

        def audio_callback(data, frames, time, status):
            nonlocal state, counter
            if status:
                print(status, file=sys.stderr)

            energy = 0 if self.muted else audioop.rms(data, 2)
            # print(energy)
            is_speech = energy > self.energy_threshold
            if state == 0:  # Waiting for beginning of a phrase
                queue.append(data[:])
                if len(queue) > min_speech_blocks:
                    queue.popleft()
                if is_speech:
                    counter += 1
                    if counter == min_speech_blocks:
                        state = 1
                        print('-> 1')
                else:
                    counter = 0
            elif state == 1:  # Recording speech, waiting for the end of the phrase
                queue.append(data[:])
                if is_speech:
                    counter = 0
                else:
                    counter += 1
                    if counter == min_pause_blocks:
                        for _ in range(min_pause_blocks - 1):  # Keep the last block
                            queue.pop()
                        callback(b''.join(queue))
                        queue.clear()
                        counter = 0
                        state = 0
                        print('-> 0')

        stream = sd.RawInputStream(dtype='int16', samplerate=Recognizer.SAMPLERATE, blocksize=1024,
                                   channels=Recognizer.CHANNELS,
                                   callback=audio_callback)

        min_speech_blocks = int(math.ceil(self.speech_threshold * stream.samplerate / stream.blocksize))
        min_pause_blocks = int(math.ceil(self.pause_threshold * stream.samplerate / stream.blocksize))

        with stream:
            yield stream
