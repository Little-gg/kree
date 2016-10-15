#!/usr/bin/env python
# encoding: utf-8

from queue import Rds
from celery import task
from config.logger import Log
from tools.path_utils import get_playbooks_dir
from main import app
import ast
import re
import datetime

log = Log.getLogger(__name__)

class Time(object):
    def __new__(cls):
        return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

def get_playbooks_list():
    return get_playbooks_dir()


def get_job_details(task_id):
    log = Log.getLogger(__name__ + '.get_job_details')
    log.debug("Entering get job detailes function.")
    rds = Rds("job-" + task_id)
    job_details = rds.getter()
    #  job_details = eval_json_data(job_details)
    return job_details

#  def get_current_task_result(task_id):
    #  log = Log.getLogger(__name__ + '.get_current_task_result')
    #  log.debug("Entering get current task result function.")
    #  return 'running', ''

def eval_json_data(data):
    if type(dict(data)) == type({}):
        return dict(data)
    elif type(ast.literal_eval(data)) == type({}):
        return ast.literal_eval(data)
    elif type(ast.literal_eval(ast.literal_eval(data))) == type({}):
        return ast.literal_eval(ast.literal_eval(data))
    else:
        raise Exception("failed to parse json.")

def parse_raw_log_output(raw_log_output):
    log = Log.getLogger(__name__ + '.parse_raw_log_output')
    log.debug("Starting parse raw log output to JSON format.")
    log_pointer_len = len(raw_log_output)
    for log_pointer in range(0, log_pointer_len):
        log.debug(raw_log_output[log_pointer])
        if re.match("^TASK:", raw_log_output[log_pointer]):
            log.debug("Match: raw_log_output[log_pointer]")
            for log_pointer_inner in range(log_pointer, log_pointer_len):
                pass


def get_raw_log_output(task_id):
    log = Log.getLogger(__name__ + '.get_raw_log_output')
    log.debug("Starting to get raw log output.")
    raw_log_output=[]
    raw_log_filehandler = app.config['STDOUT_DIR'] + '/' + task_id + '.log'
    fh = open(raw_log_filehandler, 'r')
    for line in fh.readlines():
        raw_log_output.append(line)
    log.debug("Raw log output: %s" % raw_log_output)
    return raw_log_output
