class FileDecoder:
    pass

class StreamDecoder:
    pass

import subprocess

import re
from threading import Thread

from decoder import Decoder


class KaldiDecoder(Decoder):
    def __init__(self, model_dir):
        super().__init__()
        self._model_dir = model_dir
        self._process = None
        self._running = False
        self._reading_thread = None

    def initialize(self):
        self._running = True
        self._process = subprocess.Popen(['./decoding/kaldi-gmm-live-decoder',
                                         '--config=/home/jfajkowski/Projects/asr-system/asr-builder/builds/pl-PL/0.0.3/exp/tri3b/conf/online_decoding.conf',
                                         '--word-symbol-table=/home/jfajkowski/Projects/asr-system/asr-builder/builds/pl-PL/0.0.3/exp/tri3b/graph/words.txt',
                                         '/home/jfajkowski/Projects/asr-system/asr-builder/builds/pl-PL/0.0.3/exp/tri3b/graph/HCLG.fst',
                                         'ark:echo SPEAKER UTTERANCE|',
                                         'scp:-',
                                         'ark:/dev/null'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self._reading_thread = Thread(target=self._read)
        self._reading_thread.start()

    def decode(self, wav_file):
        self._process.stdin.write('{}\t{}\n'.format(wav_file, wav_file).encode('UTF-8'))
        self._process.stdin.flush()
        self._decoding_queue.put(wav_file)

    def _read(self):
        while self._running:
            wav_file = self._decoding_queue.get(block=True)

            while True:
                result = self._process.stdout.readline().decode('UTF-8')
                match = re.findall(r'^{} (.+)'.format(wav_file), result)
                if match:
                    print(match[0].capitalize().strip() + '.')
                    break
