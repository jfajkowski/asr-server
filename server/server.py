import uuid

import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, tornado.tcpserver
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.options import define, options

import decoding

define("http_port", default=10000, help="run on the given port", type=int)
define("tcp_port", default=10001, help="run on the given port", type=int)


class TranscriptionHTTPServer(tornado.httpserver.HTTPServer):
    def __new__(cls, *args, **kwargs):
        application = tornado.web.Application([
            (r"/", IndexHandler),
            (r"/upload", UploadHandler)
        ])
        return super().__new__(cls, application)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/upload_form.html")


class UploadHandler(tornado.web.RequestHandler):
    decoder = decoding.FileDecoder()

    def post(self):
        wav_file = self.request.files['wav_file'][0]
        wav_path = "./uploads/" + UploadHandler._unique_filename()
        with open(wav_path, 'wb') as f_out:
            f_out.write(wav_file['body'])
        self.finish(UploadHandler.decoder.decode(wav_path))

    @staticmethod
    def _unique_filename():
        return str(uuid.uuid4())


class TranscriptionTCPServer(tornado.tcpserver.TCPServer):
    clients = set()

    @gen.coroutine
    def handle_stream(self, stream, address):
        ip, fileno = address
        print("Incoming connection from " + ip)
        TranscriptionTCPServer.clients.add(address)
        while True:
            try:
                yield self.echo(stream)
            except StreamClosedError:
                print("Client " + str(address) + " left.")
                TranscriptionTCPServer.clients.remove(address)
                break

    @gen.coroutine
    def echo(self, stream):
        data = yield stream.read_until('\n'.encode(options.encoding))
        print('Echoing data: ' + repr(data))
        yield stream.write(data)


def main():
    http_server = TranscriptionHTTPServer()
    http_server.listen(options.http_port)
    tcp_server = TranscriptionTCPServer()
    tcp_server.listen(options.tcp_port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
