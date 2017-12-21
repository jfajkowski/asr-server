from abc import ABC, abstractmethod
import json
from threading import Timer
from typing import List

import tornado.ioloop
import tornado.tcpclient
from tornado import gen
from tornado.iostream import StreamClosedError

from messages import Transcription, MESSAGE_SEPARATOR


class DecodingEvent:
    __slots__ = ('transcription')

    def __init__(self, transcription: Transcription):
        self.transcription = transcription


class DecodingListener(ABC):
    @abstractmethod
    def on_decoding(self, decoding_event: DecodingEvent):
        pass


class DecodingTCPClient(tornado.tcpclient.TCPClient):
    def __init__(self, host, port):
        super().__init__()
        self.__host = host
        self.__port = port
        self.__stream = None
        self.__decoding_listeners: List[DecodingListener] = []
        self.__decoding = False

    @property
    def is_decoding(self):
        return self.__decoding

    def add_recording_listener(self, decoding_listener: DecodingListener):
        self.__decoding_listeners.append(decoding_listener)


    def decode(self, frames):
        if self.is_decoding:
            self.__stream.write(frames)
        else:
            raise RuntimeError('Client is disconnected!')

    @gen.coroutine
    def run(self):
        try:
            self.__stream = yield self.connect(self.__host, self.__port)
            self.__decoding = True

            while self.__decoding:
                data = yield self.__stream.read_until(MESSAGE_SEPARATOR)
                body = data.rstrip(MESSAGE_SEPARATOR).decode('UTF-8')
                message = json.loads(body)
                transcription = Transcription(*message)
                for decoding_listener in self.__decoding_listeners:
                    decoding_event = DecodingEvent(transcription)
                    decoding_listener.on_decoding(decoding_event)

        except StreamClosedError:
            self.__stream = None
            self.__decoding = False


@gen.coroutine
def main():
    client = DecodingTCPClient('127.0.0.1', 10001)
    client.run()
    yield send(client)


@gen.coroutine
def send(client):
    import wave
    with wave.open('../1.wav', mode='rb') as f_in:
        nframes = f_in.getnframes()
        frames = f_in.readframes(nframes)
        client.decode(frames)

if __name__ == '__main__':
    main()
    tornado.ioloop.IOLoop.instance().start()
