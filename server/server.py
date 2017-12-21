import json
import uuid

import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, tornado.tcpserver
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.options import define, options

import decoding
from messages import Transcription, MESSAGE_SEPARATOR

define('http_port', default=10000, help='run on the given port', type=int)
define('tcp_port', default=10001, help='run on the given port', type=int)
define('encoding', default='UTF-8', help='encoding of hypotheses', type=str)


class DecodingHTTPServer(tornado.httpserver.HTTPServer):
    def __new__(cls, *args, **kwargs):
        application = tornado.web.Application([
            (r'/', IndexHandler),
            (r'/upload', UploadHandler)
        ])
        return super().__new__(cls, application)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')


class UploadHandler(tornado.web.RequestHandler):
    decoder = decoding.FileDecoder()

    def post(self):
        wav_file = self.request.files['wav_file'][0]
        wav_path = './uploads/' + UploadHandler._unique_filename()
        with open(wav_path, 'wb') as f_out:
            f_out.write(wav_file['body'])
        self.finish(UploadHandler.decoder.decode(wav_path))

    @staticmethod
    def _unique_filename():
        return str(uuid.uuid4())


class DecodingTCPServer(tornado.tcpserver.TCPServer):
    def __init__(self):
        super().__init__(read_chunk_size=1024)
        self.__clients = set()

    @gen.coroutine
    def handle_stream(self, stream, address):
        self.__clients.add(address)
        print('Client {} joined.'.format(address))
        decoder = decoding.StreamDecoder(lambda s: self.notify(stream, s))

        try:
            yield stream.read_until_close(decoder.decode)
        except StreamClosedError:
            print('Client {} left.'.format(address))
            self.__clients.remove(address)

    @gen.coroutine
    def notify(self, stream, sentence):
        transcription = Transcription(sentence)
        message = transcription.to_dict()
        body = json.dumps(message)
        data = (body + MESSAGE_SEPARATOR).decode('UTF-8')
        yield stream.write(data)


def main():
    http_server = DecodingHTTPServer()
    http_server.listen(options.http_port)
    tcp_server = DecodingTCPServer()
    tcp_server.listen(options.tcp_port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
