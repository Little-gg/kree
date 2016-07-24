#!/usr/bin/env python
# encoding: utf-8

from . import celery
import subprocess
import sys


def invoke(job, cmd):
    task = invoke_task.apply_async(args=[job.stream_file, cmd])
    task_id = task.task_id
    task_state = task.state
    invoke_task.update_state(task_id=task_id, state='RUNNING', meta={'stream_file': job.stream_file})
    return task_id, task_state


@celery.task
def invoke_task(job_stream_file, cmd):
    result = execute(cmd, job_stream_file)
    return result


def execute(command, stream):
    f = open(stream, 'w')
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sys.stdout = f
    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()
    sys.stdout = sys.__stdout__
    f.close()

    f = open(stream, 'r')
    output = f.readlines()
    f.close()

    return output


@celery.task
def check_task_result(task_id):
    task = check_task_result.AsyncResult(task_id)
    result = ''
    if task._get_task_meta().get('status') == 'RUNNING':
        stream = task._get_task_meta()['result'].get('stream_file')
        f = open(stream, 'r')
        result = f.readlines()
    else:
        result = task.get()
    state = task.state
    return result, state
