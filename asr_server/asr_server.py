import uuid

import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/upload", UploadHandler)
        ]
        tornado.web.Application.__init__(self, handlers)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/upload_form.html")


class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        wav_file = self.request.files['wav_file'][0]
        with open("uploads/" + UploadHandler._unique_filename(), 'wb') as f_out:
            f_out.write(wav_file['body'])
        self.finish("Transcription: ")

    @staticmethod
    def _unique_filename():
        return str(uuid.uuid4())

def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
