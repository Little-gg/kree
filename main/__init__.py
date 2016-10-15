#!/usr/bin/env python
# encoding: utf-8

import types
from flask_restful import Api
from flask import Flask
from config.logger import Log

log = Log.getLogger(__name__)

app = Flask(__name__)
api = Api(app)
app.config.from_pyfile('config/config.py')


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper


api.route = types.MethodType(api_route, api)


from task_server import make_celery
celery = make_celery(app)
from routes import *
