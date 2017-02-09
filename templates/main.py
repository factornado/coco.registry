import yaml
import os
import bson
from tornado import ioloop, web, httpserver, httpclient, httputil
import pandas as pd
import logging

from utils import Config

config = Config('config.yml')

logging.basicConfig(
    level=10,
    filename=config.conf['log.file'],
    format='%(asctime)s (%(filename)s:%(lineno)s)- %(levelname)s - %(message)s',
    )

logging.info('='*80)


class Info(web.RequestHandler):
    def get(self):
        self.write(config.conf)


class RegisterHandler(web.RequestHandler):
    """Register a new service."""
    def post(self, name=None, version=None):
        body = pd.json.loads(self.request.body)
        if 'url' not in body:
            raise web.HTTPError(500, 'body must at least contain `url`.')
        doc = {'id': bson.ObjectId(),
               '_id': body.pop('url'),
               'name': name,
               'version': version,
               'info': body,
               }
        replace = config.mongo.host01.db01.collection01.replace_one(
            {'_id': doc['_id']}, doc, upsert=True)
        self.write('ok')
    def get(self, name=None, version=None):
        confs = list(config.mongo.host01.db01.collection01.find({'name': name, 'version': version}))
        self.write({name: {version: confs}})


class GetAllHandler(web.RequestHandler):
    """Get the list of all registered services."""
    def get(self, param=''):
        data = pd.DataFrame([{'name': x['name'], 'version': x['version'], 'doc': x}
                             for x in config.mongo.host01.db01.collection01.find()])
        self.write({name: {version: subgroup['doc'].tolist()
                           for version, subgroup in group.groupby('version')}
                    for name, group in data.groupby('name')}
                   )


class ProxyHandler(web.RequestHandler):
    @web.asynchronous
    def redirection(self, method, name, version):
        # Get the service configuration.
        confs = list(config.mongo.host01.db01.collection01.find(
                {'name': name, 'version': version},
                sort=[('id', -1)]))  # We get the most recent heartbeat first.
        if len(confs) == 0:
            raise web.HTTPError(500, reason='Service {} not known.'.format(service))
        conf = confs[0]  # TODO: create round_robin here.

        url = conf.get('_id', None)
        if url is None:
            raise web.HTTPError(500, reason='Service {} has no url.'.format(service))
        user = conf.get('info', {}).get('user', None)
        password = conf.get('info', {}).get('password', None)

        # Parse the uri.
        uri = self.request.uri[1:]
        if not uri.startswith(name+'/'+version):
            raise web.HTTPError(
                500,
                reason='Uri {} does not start with {}.'.format(uri, name+'/'+version))
        uri = uri[len(name+'/'+version):]

        # Proxy the request.
        request = httpclient.HTTPRequest(
            url + uri,
            method=method,
            headers=httputil.HTTPHeaders({
                k: v for k, v in self.request.headers.get_all()
                if k.lower() != 'host'
                }),
            body=self.request.body,
            auth_username=user,
            auth_password=password,
            allow_nonstandard_methods=True,
            request_timeout=300.,
            validate_cert=False,
            )
        httpclient.AsyncHTTPClient().fetch(request, self.on_response)
        # response = httpclient.HTTPClient().fetch(request)
        # self.write(response.body)

    @web.asynchronous
    def get(self, name, version, uri=''):
        self.redirection('GET', name, version)

    @web.asynchronous
    def post(self, name, version, uri=''):
        self.redirection('POST', name, version)

    @web.asynchronous
    def put(self, name, version, uri=''):
        self.redirection('PUT', name, version)

    def on_response(self, response):
        if response.code == 304:
            self.set_status(304)
            self.finish()
            return

        if response.error is not None:
            raise web.HTTPError(response.code, reason=response.reason)

        self.set_status(response.code)

        for key, val in response.headers.get_all():
            if key not in ['Transfer-Encoding', 'Content-Encoding']:
                self.add_header(key, val)

        if response.body:
            self.write(response.body)
        self.finish()


class SwaggerHandler(web.RequestHandler):
    def get(self):
        data = pd.DataFrame([{'name': x['name'], 'version': x['version'], 'doc': x}
                             for x in config.mongo.host01.db01.collection01.find()])
        self.write({
            'apiVersion': '1.0',
            'apis': [
                {
                    'description': '/'.join((name,version)),
                    'path': '/{}/{}/swagger.json'.format(name,version),
                    'position': i,
                    } for i, ((name, version), _) in enumerate(data.groupby(['name', 'version']))],
            'authorizations': {},
            'info': {
                'contact': 'Contact Martin Journois (Michelin solutions) or Nicolas Roux (Agaetis)',  # noqa
                'description': 'API for arabica',
                'license': 'Property of Michelin solutions®',
                'licenseUrl': '-',
                'termsOfServiceUrl': 'API strictly reserved to Michelin solutions® internal applications',  # noqa
                'title': 'Michelin solutions® FleetScience API',
                },
            'swaggerVersion': '1.2',
            })


app = web.Application([
    ("", SwaggerHandler),
    ("/", SwaggerHandler),
    ("/info", Info),
    ("/(swagger)", web.StaticFileHandler, {'path': os.path.dirname(__file__)}),
    ("/register/all", GetAllHandler),
    ("/register/([^/]*?)/([^/]*?)", RegisterHandler),
    ("/([^/]*?)/([^/]*?)/(.*)", ProxyHandler),
    ("/([^/]*?)/([^/]*?)", ProxyHandler),
    ])

if __name__ == "__main__":
    port = config.get_port()
    logging.info('Listening on port', port)

    server = httpserver.HTTPServer(app)
    server.bind(port, address='0.0.0.0')
    server.start(config.conf['threads_nb'])
    ioloop.IOLoop.current().start()
