import argparse
import time
import wave

import librosa
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from librosa.display import TimeFormatter
from scipy.fftpack import hilbert, rfft

from recorder import RecordingListener, RecordingEvent, Recorder


class Plotter(RecordingListener):
    SAMPLE_FORMAT = pyaudio.paInt16

    def __init__(self, max_fps=60, window_size=100000, sample_rate=16000,
                 signal_min_y_axis=1):
        super().__init__()
        self.__engine = pyaudio.PyAudio()
        self.__min_interval = 1 / max_fps
        self.__prev_time = time.time()
        self.__signal_min_y_axis = signal_min_y_axis
        self.__sample_rate = sample_rate
        self.__max_frequency = int(sample_rate / 2)
        self.__window_size = window_size
        self.__sample_size = self.__engine.get_sample_size(Plotter.SAMPLE_FORMAT)
        self.__samples = bytearray()
        self.__chunk_size = window_size * self.__sample_size

    @property
    def is_plotting(self):
        return plt.get_fignums()

    def plot(self):
        self.initialize()
        while self.is_plotting:
            if len(self.__samples) > self.__chunk_size:
                samples = self.__samples[-self.__chunk_size:]
                signal = np.frombuffer(samples, dtype=np.int16)
                self.update(signal)
            self.maintain_fps()

    def initialize(self):
        self.__fig = plt.subplots(3, 1)[0]
        plt.ion()
        plt.legend()
        # plt.tight_layout()
        plt.show()

    def update(self, signal):
        normalized_signal = signal / np.max(signal)
        signal_spectrogram = np.abs(librosa.stft(signal)) ** 2
        features = librosa.feature.mfcc(S=librosa.power_to_db(librosa.feature.melspectrogram(S=signal_spectrogram)))


        plt.subplot(3, 1, 1)
        plt.cla()
        librosa.display.waveplot(normalized_signal, sr=self.__sample_rate, x_axis='off')
        plt.ylabel('Amplituda')
        plt.subplot(3, 1, 2)
        librosa.display.specshow(librosa.amplitude_to_db(signal_spectrogram, ref=np.max), y_axis='log')
        plt.subplot(3, 1, 3)
        librosa.display.specshow(features, x_axis='time', y_axis='frames')
        plt.xlabel('Czas [s]')
        plt.ylabel('Numer\nwspółczynnika MFCC')
        self.refresh()

    def refresh(self):
        self.__fig.canvas.flush_events()

    def maintain_fps(self):
        difference = self.__min_interval - (time.time() - self.__prev_time)
        self.__prev_time = time.time()
        if difference > 0:
            time.sleep(difference)

    def on_recording(self, recording_event: RecordingEvent):
        self.__samples += recording_event.samples


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('wav_files', metavar='WAV_FILES', nargs='*', default='')
    return parser.parse_args()

def live_plot():
    plotter = Plotter()
    recorder = Recorder()
    recorder.add_recording_listener(plotter)
    recorder.record()
    plotter.plot()
    recorder.stop()

def file_plot(wav_file):
    with wave.open(wav_file, mode='rb') as f_in:
        sample_size = f_in.getsampwidth()
        samples = f_in.readframes(-1)
        signal = np.frombuffer(samples, dtype=np.int16)

        plotter = Plotter(window_size=int(len(samples) / sample_size))
        plotter.initialize()
        plotter.update(signal)

        while plotter.is_plotting:
            plotter.refresh()


if __name__ == '__main__':
    args = parse_args()

    if args.wav_files:
        for i, wav_file in enumerate(args.wav_files):
            print('{}/{}'.format(i + 1, len(args.wav_files)))
            file_plot(wav_file)
    else:
        live_plot()
