#!/usr/bin/env python
# encoding: utf-8

from flask_restful import Api
from flask import Flask
import types
import sys


app = Flask(__name__)
api = Api(app)
app.config.from_pyfile('config.py')


import logging
app.logger.addHandler(logging.StreamHandler(sys.stdout))
logger = app.logger


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper


api.route = types.MethodType(api_route, api)


from plugin import make_celery
celery = make_celery(app)
from routes import *

