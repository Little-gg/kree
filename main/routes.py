#!/usr/bin/env python
# encoding: utf-8

from time import sleep
from flask_restful import Resource
from flask import request
from . import api
from config.logger import Log
from helpers import get_job_details, get_raw_log_output, get_playbooks_list
from queue import Rds
from tasks import RunJob
from uuid import uuid4
import json

log = Log.getLogger(__name__)


@api.route('/')
class List_Playbooks(Resource):
    def get(self):
        playbooks_list = get_playbooks_list()
        return {'playbooks': playbooks_list}


@api.route('/<playbook>')
class Playbook(Resource):
    def post(self, playbook):
        log.debug("Inovke run playbook task.")
        job_params = request.get_json()
        job_params['playbook'] = playbook
        task_id = str(uuid4())
        job = RunJob()
        result = job.apply_async(args=[job_params], task_id = task_id, time_limit=86400)

        # celery task is a asynchronous call, so add a wait for redis to get message
        sleep(0.1)
        job_details = get_job_details(task_id)

        log.debug("Job details: %s" % job_details)

        return {
                'playbook': job_details['playbook'],
                'task_id': job_details['task_id']
                }

    def get(self, playbook):
        return


@api.route('/<playbook>/detail')
class Playbook_Detail(Resource):
    def get(self, playbook):
        raise NotImplementedError


@api.route('/task')
class List_tasks(Resource):
    def get(self):
        raise NotImplementedError


@api.route('/task/<task_id>')
class Task_Detail(Resource):
    def get(self, task_id):
        log.debug("Inovke task result inspecting.")

        ######
        # step 1: get raw log
        raw_log_output = get_raw_log_output(task_id)

        ######
        # step 2: get result from db
        job_details = get_job_details(task_id)

        return {
                   'job_task_id': task_id,
                   'raw_log_output': raw_log_output,
                   'job_details': job_details,
                }


@api.route('/callback/<task_id>')
class Callback(Resource):
    def get(self, task_id):
        log = Log.getLogger(__name__ + ".Callback.get")
        queue = Rds('job-' + task_id)
        queue_data = queue.getter()
        log.debug("Task event callback called: %s %s" % (task_id, json.dumps(queue_data)))

    def post(self, task_id):
        log = Log.getLogger(__name__ + ".Callback.post")
        data = {}
        data = request.get_json()
        queue = Rds('job-' + task_id)
        log.debug(queue._key_name)
        queue_data = queue.getter()
        step_result_id = len(queue_data['step_result']) + 1
        queue_data['step_result'][step_result_id] = data
        queue_data['update_time'] = data['timestamp']
        if data.has_key('result'):
            queue_data['result'] = data['result']
        queue.setter(queue_data)
        log.debug("Task event updated from callback: %s %s" % (task_id, json.dumps(queue_data)))
        #  log.debug(data)

