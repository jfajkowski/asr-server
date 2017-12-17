import re
import subprocess


class FileDecoder:
    def __init__(self):
        self._process = subprocess.Popen(['./file-decoder',
                                          '--config=./model/online_decoding.conf',
                                          './model/words.txt',
                                          './model/HCLG.fst',
                                          'scp:-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def decode(self, wav_path):
        self._write(wav_path)
        transcription = self._read(wav_path)
        return transcription

    def _write(self, wav_path):
        self._process.stdin.write('{}\t{}\n'.format(wav_path, wav_path).encode('UTF-8'))
        self._process.stdin.flush()

    def _read(self, wav_path):
        while True:
            result = self._process.stdout.readline().decode('UTF-8')
            match = re.findall(r'^{}\t(.+)'.format(wav_path), result)
            if match:
                return match[0].strip()
