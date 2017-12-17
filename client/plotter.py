import time
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy.fftpack import hilbert

from recorder import RecordingListener, RecordingEvent


class Plotter(RecordingListener):
    def __init__(self, max_fps=120, samples_per_window=2048, window_height=10000, sample_format=pyaudio.paInt16):
        super().__init__()
        self.__engine = pyaudio.PyAudio()
        self.__min_interval = 1 / max_fps
        self.__prev_time = time.time()
        self.__window_height = window_height
        self.__samples_per_window = samples_per_window
        self.__sample_size = self.__engine.get_sample_size(sample_format)
        self.__samples = bytearray()
        self.__window_size = samples_per_window * self.__sample_size

    @property
    def plotting(self):
        return plt.get_fignums()

    def show_plot(self):
        fig, signal_line, envelope_line = self.init_plot()
        while self.plotting:
            if len(self.__samples) > self.__window_size:
                self.update_plot(fig, signal_line, envelope_line)
            self.maintain_fps()

    def init_plot(self):
        fig, ax = plt.subplots()
        ax.set_xlim(0, self.__samples_per_window)
        ax.set_ylim(-self.__window_height / 2, self.__window_height / 2)
        signal_line = ax.plot(np.arange(self.__samples_per_window),
                              np.zeros(self.__samples_per_window), label='signal')[0]
        envelope_line = ax.plot(np.arange(self.__samples_per_window),
                                np.zeros(self.__samples_per_window), label='envelope')[0]
        plt.ion()
        plt.legend()
        plt.show()
        return fig, signal_line, envelope_line

    def update_plot(self, fig, signal_line, envelope_line):
        samples = self.__samples[-self.__window_size:]
        signal = np.fromstring(str(bytes(samples)), 'Int16')
        analytical_signal = hilbert(signal)
        amplitude_envelope = np.abs(analytical_signal)

        signal_line.set_ydata(signal)
        envelope_line.set_ydata(amplitude_envelope)
        fig.canvas.flush_events()

    def maintain_fps(self):
        difference = self.__min_interval - (time.time() - self.__prev_time)
        self.__prev_time = time.time()
        if difference > 0:
            time.sleep(difference)

    def on_recording(self, recording_event: RecordingEvent):
        self.__samples += recording_event.samples
