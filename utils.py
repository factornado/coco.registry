import socket
import yaml
import pymongo


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


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
