import json
import socket
import struct
import logging
import ipaddress
from abc import ABC, abstractmethod
from threading import Thread
from typing import List

import multiprocessing
from queue import Empty

from recorder import RecordingListener, RecordingEvent


class HypothesisEvent(ABC):
    __slots__ = ('backoff', 'phrase')

    def __init__(self, backoff: int, phrase: str):
        self.backoff = backoff
        self.phrase = phrase


class HypothesisListener(ABC):
    @abstractmethod
    def on_hypothesis(self, hypothesis_event: HypothesisEvent):
        pass


class StreamingClient(RecordingListener):
    HEADER_FORMAT = '!H'
    BUFFERSIZE = 1024
    TIMEOUT = 1

    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        self.__online = False
        self.__socket = None
        self.__hypothesis_thread = None
        self.__hypothesis_listeners: List[HypothesisListener] = []

    @property
    def online(self):
        return self.__online

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.settimeout(StreamingClient.TIMEOUT)
        self.__online = True
        self.__hypothesis_thread = Thread(target=self.__hypothesis_callback)
        self.__hypothesis_thread.start()
        logging.info('StreamingClient started.')

    def stop(self):
        if self.__online:
            self.__online = False
            self.__hypothesis_thread.join()
            self.__hypothesis_thread = None
            self.__socket.close()
            self.__socket = None
            logging.info('StreamingClient stopped.')

    def on_recording(self, recording_event: RecordingEvent):
        if self.__online:
            self.__send_samples(recording_event.samples)

    def __send_samples(self, samples):
        self.__socket.sendto(samples, (self.__host, self.__port))

    def add_hypothesis_listener(self, hypothesis_listener: HypothesisListener):
        self.__hypothesis_listeners.append(hypothesis_listener)

    def __hypothesis_callback(self):
        while self.__online:
            try:
                header_bytes_len = struct.calcsize(StreamingClient.HEADER_FORMAT)
                header_bytes = self.__socket.recv(header_bytes_len)

                json_bytes_len = struct.unpack(StreamingClient.HEADER_FORMAT, header_bytes)[0]
                json_bytes = bytes()
                while len(json_bytes) < json_bytes_len:
                    buffer = self.__socket.recv(StreamingClient.BUFFERSIZE)
                    json_bytes += buffer
                json_dict = json.loads(json_bytes.decode())
                hypothesis_event = HypothesisEvent(*json_dict)
                for hypothesis_listener in self.__hypothesis_listeners:
                    hypothesis_listener.on_hypothesis(hypothesis_event)
            except socket.timeout:
                pass


class StreamingServer:
    HEADER_FORMAT = '!H'
    BUFFERSIZE = 1024
    TIMEOUT = 1

    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        self.__online = False
        self.__samples_socket = None
        self.__samples_thread = None
        self.__hypothesis_socket = None
        self.__hypothesis_thread = None
        self.__queue = multiprocessing.Queue()

    @property
    def online(self):
        return self.__online

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        self.__samples_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__samples_socket.settimeout(StreamingServer.TIMEOUT)
        self.__samples_socket.bind((self.__host, self.__port))
        self.__hypothesis_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__online = True
        self.__samples_thread = Thread(target=self.__samples_callback)
        self.__samples_thread.start()
        self.__hypothesis_thread = Thread(target=self.__hypothesis_callback)
        self.__hypothesis_thread.start()
        logging.info('StreamingServer started.')

    def stop(self):
        if self.__online:
            self.__online = False
            self.__samples_thread.join()
            self.__samples_thread = None
            self.__hypothesis_thread.join()
            self.__hypothesis_thread = None
            self.__samples_socket.close()
            self.__samples_socket = None
            self.__hypothesis_socket.close()
            self.__hypothesis_socket = None
            logging.info('StreamingServer stopped.')

    def __samples_callback(self):
        while self.online:
            try:
                samples, address = self.__samples_socket.recvfrom(StreamingServer.BUFFERSIZE)
                self.__queue.put((samples, address), timeout=StreamingServer.TIMEOUT)
            except socket.timeout:
                pass

    def __hypothesis_callback(self):
        while self.__online:
            try:
                hypothesis, address = self.__queue.get(timeout=StreamingServer.TIMEOUT)
                json_bytes = json.dumps({'backoff': 1, 'phrase': ''}).encode()
                json_bytes_len = len(json_bytes)
                header_bytes = struct.pack(StreamingServer.HEADER_FORMAT, json_bytes_len)
                self.__hypothesis_socket.sendto(header_bytes, address)
                self.__hypothesis_socket.sendto(json_bytes, address)
            except Empty:
                pass


if __name__ == '__main__':
    logging.basicConfig(format='[%(levelname)s][%(asctime)s]: %(message)s', level=logging.INFO)
    with StreamingServer('', 10000) as s, StreamingClient('127.0.0.1', 10000) as c:
        i = 0
        for i in range(10000):
            r = RecordingEvent(1024 * bytes(), None, None, None)
            c.on_recording(r)
            i += 1
