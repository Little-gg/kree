#!/usr/bin/env python
# encoding: utf-8

from flask_restful import Resource
from flask import request
from . import api
from . import *
from . import logger
from dict2obj import dict2obj
from models import NullJob, NoParamJob, Job, Task


@api.route('/')
class List_playbooks(Resource):
    def get(self):
        job = NullJob()
        return {'playbook': job.available_playbooks()}


@api.route('/<playbook>/detail')
class Playbook_detail(Resource):
    def get(self, playbook):
        job = NoParamJob(playbook)
        return {'name': playbook, 'description': job.get_detail(),
                'available_methods': job.available_methods()}


@api.route('/task')
class List_tasks(Resource):
    def get(self):
        raise NotImplementedError


@api.route('/task/<task_id>')
class Task_detail(Resource):
    def get(self, task_id):
        task = Task(task_id)
        result, state = task.get_task_detail()
        return {'id': task_id, 'result': result, 'state': state}


@api.route('/<playbook>')
class Playbook(Resource):
    def post(self, playbook):
        req = dict2obj(request.get_json())
        job = Job(playbook, req)
        if not job.validate_playbook_existance():
            return {'error': 'Playbook %s not exist!' % playbook}
        if not req.has_key('method'):
            return {'error': 'Missing playbook method!'}

        method = req.get('method')
        task_id, task_state = job.run(method)
        return {'name': playbook, 'id': task_id, 'state': task_state}

    def get(self, playbook):
        job = NoParamJob(playbook)
        return {'name': playbook, 'description': job.get_detail()}
