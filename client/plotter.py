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

    def __init__(self, max_fps=60, window_size=4096, sample_rate=16000,
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

        self.__fig = None
        self.__axes = None
        self.__signal_line = None
        self.__envelope_line = None
        self.__spectrum_line = None
        self.__mfcc_line = None

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
        self.__fig, self.__axes = plt.subplots(2, 2)

        ax = self.__axes[0, 0]
        ax.set_xlim(xmax=self.__window_size)
        ax.set_ylim(-self.__signal_min_y_axis, self.__signal_min_y_axis)
        self.__signal_line = ax.plot(np.arange(self.__window_size),
                                     np.zeros(self.__window_size), label='signal')[0]
        self.__envelope_line = ax.plot(np.arange(self.__window_size),
                                       np.zeros(self.__window_size), label='envelope')[0]

        ax = self.__axes[1, 0]
        ax.set_xscale('log')
        ax.set_xlim(xmax=self.__max_frequency)
        ax.set_ylim(ymax=self.__signal_min_y_axis)
        self.__spectrum_line = ax.plot(np.arange(self.__max_frequency),
                                       np.zeros(self.__max_frequency), label='fft')[0]

        ax = self.__axes[0, 1]
        ax.xaxis.set_major_formatter(TimeFormatter())

        plt.ion()
        plt.legend()
        plt.tight_layout()
        plt.show()

    def update(self, signal):
        signal_max = np.max(signal)
        signal_envelope = np.abs(hilbert(signal))
        spectrum = np.abs(rfft(signal, self.__max_frequency))
        spectrum_max = np.max(spectrum)
        normalized_spectrum = spectrum / spectrum_max
        signal_spectrogram = np.abs(librosa.stft(signal)) ** 2
        features = librosa.feature.mfcc(S=librosa.power_to_db(librosa.feature.melspectrogram(S=signal_spectrogram)))


        if signal_max > self.__signal_min_y_axis:
            self.__signal_min_y_axis = signal_max
            self.__axes[0, 0].set_ylim(-self.__signal_min_y_axis, self.__signal_min_y_axis)

        plt.subplot(2, 2, 2)
        librosa.display.specshow(librosa.amplitude_to_db(signal_spectrogram, ref=np.max), y_axis='log', x_axis = 'time')
        plt.subplot(2, 2, 4)
        librosa.display.specshow(features, x_axis = 'time')



        self.__signal_line.set_ydata(signal)
        self.__envelope_line.set_ydata(signal_envelope)
        self.__spectrum_line.set_ydata(normalized_spectrum)
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
