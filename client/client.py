import logging
from abc import ABC, abstractmethod
from typing import List

import tornado.tcpclient
from tornado import gen, ioloop
from tornado.websocket import websocket_connect

from messages import Transcription
from plotter import Plotter
from recorder import RecordingListener, RecordingEvent, Recorder


class DecodingEvent:
    __slots__ = ('transcription')

    def __init__(self, transcription: Transcription):
        self.transcription = transcription


class DecodingListener(ABC):
    @abstractmethod
    def on_decoding(self, decoding_event: DecodingEvent):
        pass


class WebSocketClient(ABC):
    def __init__(self, url):
        self.url = url
        self.connection = None
        self.connected = False
        self.connect()

    @gen.coroutine
    def connect(self):
        self.connection = yield websocket_connect(self.url)
        self._on_open()
        yield self._run()
        self._on_close()

    def _on_open(self):
        logging.info("connected")
        self.connected = True

    @gen.coroutine
    def _run(self):
        while self.connected:
            message = yield self.connection.read_message()
            if message:
                self._on_message(message)
            else:
                break

    @abstractmethod
    def _on_message(self, message):
        pass

    def _on_close(self):
        logging.info("disconnected")
        self.connected = False

    def write_message(self, message, binary=False):
        if self.connected:
            self.connection.write_message(message, binary)
        else:
           raise ConnectionError('connection closed')

class StreamClient(WebSocketClient, RecordingListener):
    def __init__(self, url):
        super().__init__(url)
        self.__decoding_listeners: List[DecodingListener] = []

    def add_decoding_listener(self, decoding_listener: DecodingListener):
        self.__decoding_listeners.append(decoding_listener)

    def _on_message(self, message):
        decoding_event = DecodingEvent(transcription=message)
        for decoding_listener in self.__decoding_listeners:
            decoding_listener.on_decoding(decoding_event)

    def on_recording(self, recording_event: RecordingEvent):
        self.write_message(recording_event.samples, binary=True)

class Printer(DecodingListener):
    def on_decoding(self, decoding_event: DecodingEvent):
        print(decoding_event.transcription)


def main():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s', level=logging.INFO)
    client = StreamClient('ws://localhost:10000/websocket')
    recorder = Recorder()
    plotter = Plotter()
    printer = Printer()

    recorder.add_recording_listener(client)
    recorder.add_recording_listener(plotter)
    client.add_decoding_listener(printer)

    recorder.record()
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()


