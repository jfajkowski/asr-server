import pyaudio
import wave

from abc import ABC, abstractmethod
from typing import List

import time


class RecordingEvent:
    __slots__ = ('samples', 'sample_count', 'time_info', 'status')

    def __init__(self, samples, sample_count, time_info, status):
        self.samples = samples
        self.sample_count = sample_count
        self.time_info = time_info
        self.status = status


class RecordingListener(ABC):
    @abstractmethod
    def on_recording(self, recording_event: RecordingEvent):
        pass


class Recorder:
    SAMPLE_FORMAT = pyaudio.paInt16

    def __init__(self, channels=1, sample_rate=16000, chunk_size=1024):
        self.__engine = pyaudio.PyAudio()
        self.__stream = None
        self.__recording_listeners: List[RecordingListener] = []
        self.__channels = channels
        self.__format = Recorder.SAMPLE_FORMAT
        self.__sample_rate = sample_rate
        self.__sample_size = self.__engine.get_sample_size(Recorder.SAMPLE_FORMAT)
        self.__samples = bytearray()
        self.__frames_per_buffer = int(chunk_size / self.__sample_size)

    @property
    def channels(self):
        return self.__channels

    @property
    def sample_rate(self):
        return self.__sample_rate

    @property
    def is_recording(self):
        return not self.__stream.is_stopped()

    def __enter__(self):
        self.record()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def add_recording_listener(self, recording_listener: RecordingListener):
        self.__recording_listeners.append(recording_listener)

    def record(self):
        self._initialize_recording()

    def _initialize_recording(self):
        self.__stream = self.__engine.open(format=self.__format,
                                           channels=self.__channels,
                                           rate=self.__sample_rate,
                                           frames_per_buffer=self.__frames_per_buffer,
                                           input=True,
                                           stream_callback=self._recording_callback)

    def _recording_callback(self, samples, sample_count, time_info, status):
        self.__samples += samples
        recording_event = RecordingEvent(samples, sample_count, time_info, status)
        for recording_listener in self.__recording_listeners:
            recording_listener.on_recording(recording_event)
        return None, pyaudio.paContinue

    def stop(self):
        self.__stream.stop_stream()
        self.__stream.close()

    def save(self, filename):
        with wave.open(filename, mode='wb') as f_out:
            f_out.setnchannels(self.__channels)
            f_out.setsampwidth(pyaudio.get_sample_size(self.__format))
            f_out.setframerate(self.__sample_rate)
            f_out.writeframes(self.__samples)

    def reset(self):
        self.__samples = bytearray()


if __name__ == '__main__':
    i = 1
    recorder = Recorder()
    time.sleep(1)
    while True:
        if input('Enter to start recording. Type "x" to exit: ') == 'x':
            break

        recorder.record()
        if input('Enter to stop recording. Type "r" to repeat: ') == 'r':
            recorder.stop()
            recorder.reset()
            continue

        recorder.stop()
        name = input('Enter name for file (without extension) [i]: '.format(i))

        if not name:
            name = str(i)

        recorder.save('{}.wav'.format(i))
        recorder.reset()
        i += 1
