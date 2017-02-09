import socket
import yaml
import pymongo


class Kwargs(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)


class Config(object):
    def __init__(self, filename):
        self.conf = yaml.load(open(filename))
        self.mongo = Kwargs()
        _mongo = self.conf.get('db', {}).get('mongo', {})
        self.mongo = Kwargs(**{
            hostname: Kwargs(**{
                dbname: Kwargs(**{
                    collname: pymongo.MongoClient(host['address'],
                                                  connect=False)[db['name']][coll['name']]
                    for collname, coll in _mongo.get('collection', {}).items()
                    if coll['database'] == dbname
                    })
                for dbname, db in _mongo.get('database', {}).items()
                if db['host'] == hostname
                })
            for hostname, host in _mongo.get('host', {}).items()
            })

    def get_port(self):
        if 'port' not in self.conf:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            self.conf['port'] = s.getsockname()[1]
            s.close()
        return self.conf['port']
