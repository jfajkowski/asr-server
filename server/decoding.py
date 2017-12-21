import re
import subprocess
from abc import ABC, abstractmethod


class DecodingEvent:
    __slots__ = ('transcription')

    def __init__(self, transcription):
        self.transcription = transcription


class DecodingListener(ABC):
    @abstractmethod
    def on_decoding(self, decoding_event: DecodingEvent):
        pass


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


class StreamDecoder:
    def __init__(self, callback):
        self._process = subprocess.Popen(['./stream-decoder',
                                          '--config=./model/online_decoding.conf',
                                          './model/words.txt',
                                          './model/HCLG.fst',
                                          '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self._decoding = True
        self._callback = callback

    def decode(self, frames):
        self._write(frames)
        transcription = self._read()
        return transcription

    def _write(self, frames):
        self._process.stdin.write(frames)
        self._process.stdin.flush()

    def _read(self):
        while self._decoding:
            result = self._process.stdout.readline().decode('UTF-8')
            self._callback(result.strip())


if __name__ == '__main__':
    decoder = StreamDecoder(print)

    import wave
    with wave.open('../1.wav', mode='rb') as f_in:
        nframes = f_in.getnframes()
        frames = f_in.readframes(nframes)
        decoder.decode(frames)