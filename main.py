import yaml
import os
from tornado import ioloop, web, httpserver
import pandas as pd

from utils import get_open_port, Config

config = Config('config.yml')


class Info(web.RequestHandler):
    def get(self):
        self.write(config.conf)


class RegisterHandler(web.RequestHandler):
    """Register a new service."""
    def post(self, name=None, version=None):
        doc = {'_id': self.request.body, 'name': name, 'version': version}
        replace = config.mongo.host01.db01.collection01.replace_one(
            {'_id': doc['_id']}, doc, upsert=True)
        self.write('ok')

class GetOneHandler(web.RequestHandler):
    """Get the urls for one registered service."""
    def get(self, name=None, version=None):
        self.write(
            "Asked for {}//{}\n".format(name, version))


class GetAllHandler(web.RequestHandler):
    """Get the list of all registered services."""
    def get(self, param=''):
        self.write(
            "Hello from service {}. "
            "You've asked for uri {}\n".format(
                config.conf['name'], param))

app = web.Application([
    ("/info", Info),
    ("/(swagger)", web.StaticFileHandler, {'path': os.path.dirname(__file__)}),
    ("/get/([^/]*?)/([^/]*?)", GetOneHandler),
    ("/register/([^/]*?)/([^/]*?)", RegisterHandler),
    ])

if __name__=="__main__":
    port = get_open_port()
    port = 53877
    print('Listening on port', port)

    server = httpserver.HTTPServer(app)
    server.bind(port, address='0.0.0.0')
    server.start(config.conf['threads_nb'])
    ioloop.IOLoop.current().start()