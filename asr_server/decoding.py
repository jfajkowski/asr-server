import re
import subprocess


class FileDecoder:
    def __init__(self, model_dir):
        super().__init__()
        self._model_dir = model_dir
        self._process = subprocess.Popen(['file-decoder',
                                          '--config=./model/online_decoding.conf',
                                          './model/words.txt',
                                          './model/HCLG.fst',
                                          'scp:-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def decode(self, wav_file):
        self._write(wav_file)
        transcription = self._read(wav_file)
        return transcription

    def _write(self, wav_file):
        self._process.stdin.write('{}\t{}\n'.format(wav_file, wav_file).encode('UTF-8'))
        self._process.stdin.flush()

    def _read(self, wav_file):
        while True:
            result = self._process.stdout.readline().decode('UTF-8')
            match = re.findall(r'^{} (.+)'.format(wav_file), result)
            if match:
                return match[0].capitalize().strip() + '.'
