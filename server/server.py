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

define('port', default=10000, help='run on the given port', type=int)
define('encoding', default='UTF-8', help='encoding of hypotheses', type=str)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class FileClientHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('file_client.html', hypotheses=[])


class StreamClientHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('stream_client.html')


class UploadHandler(tornado.web.RequestHandler):
    decoder = decoding.FileDecoder()

    def post(self):
        hypotheses = []
        if self.request.files:
            for file in self.request.files['wav_file']:
                wav_path = './uploads/' + UploadHandler._unique_filename()
                with open(wav_path, 'wb') as f_out:
                    f_out.write(file['body'])
                hypothesis = UploadHandler.decoder.decode(wav_path)
                hypotheses.append(hypothesis)
        self.render('file_client.html', hypotheses=hypotheses)


    @staticmethod
    def _unique_filename():
        return str(uuid.uuid4())


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.__decoder = decoding.StreamDecoder(self.write_message)
        logging.info("WebSocket opened")

    def on_message(self, message):
        self.__decoder.decode(message)

    def on_close(self):
        self.__decoder.terminate()
        logging.info("WebSocket closed")


def main():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s', level=logging.INFO)
    application = tornado.web.Application([
            (r'/', IndexHandler),
            (r'/file-client', FileClientHandler),
            (r'/stream-client', StreamClientHandler),
            (r'/upload', UploadHandler),
            (r'/websocket', WebSocketHandler)
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )

    http_server = tornado.httpserver.HTTPServer(
        application,
        ssl_options = {
            'certfile': 'new.cert.cert',
            'keyfile': 'new.cert.key'
        }
    )
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
