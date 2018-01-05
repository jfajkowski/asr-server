import logging
import uuid

import os
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.tcpserver
import tornado.web
import tornado.websocket
from tornado.options import define, options

import decoding

define('http_port', default=10000, help='run on the given port', type=int)
define('encoding', default='UTF-8', help='encoding of hypotheses', type=str)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class FileHandler(tornado.web.RequestHandler):
    decoder = decoding.FileDecoder()

    def post(self):
        wav_file = self.request.files['wav_file'][0]
        wav_path = './uploads/' + FileHandler._unique_filename()
        with open(wav_path, 'wb') as f_out:
            f_out.write(wav_file['body'])
        self.finish(FileHandler.decoder.decode(wav_path))

    @staticmethod
    def _unique_filename():
        return str(uuid.uuid4())


class StreamHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.__decoder = decoding.StreamDecoder(self.write_message)
        logging.info("WebSocket opened")

    def on_message(self, message):
        self.__decoder.decode(message)

    def on_close(self):
        del self.__decoder
        logging.info("WebSocket closed")


def main():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s', level=logging.INFO)
    application = tornado.web.Application([
            (r'/', IndexHandler),
            (r'/upload', FileHandler),
            (r'/websocket', StreamHandler)
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.http_port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
