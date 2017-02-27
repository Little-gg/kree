#!/usr/bin/env python
# encoding: utf-8

from celery import Task
#  from celery.signals import celeryd_init
from tools.path_utils import *
from tools.dict2obj import dict2obj
from queue import Rds
from config.logger import Log
from main import app
from helpers import eval_json_data, Time
import subprocess
import collections
import tempfile
import sys


log = Log.getLogger(__name__)

#  @celeryd_init
#  def celery_connectd():
    #  log.info("Celery connected.")


def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


class RunJob(Task):
    #  abstract = True
    name = __name__
    LINE_INV = '_all'
    META_CODE = '_meta'

    def _parse_params(self, params):
        try:
            log.debug("params: %s" % params)
            _formatted_params = dict2obj(params)
            if not hasattr(_formatted_params, 'inventory'):
                log.error("Missing inventory block.")
            if not ((hasattr(_formatted_params, 'username') and \
                    hasattr(_formatted_params, 'password')) or \
                    hasattr(_formatted_params, 'ssh_pubkey')):
                log.error("Missing credential block.")
        except:
            raise Exception("invalid JSON parameter input.")

        return _formatted_params


    def run(self, params, *args, **kwargs):
        log.info("Start to run job with params: %s" % params)
        params = self._remove_empty_value(params)
        self.params = self._parse_params(params)
        log.debug("%s" % self.params)
        self._save_job_details()

        ## last step: call ansible
        self._call_ansible()


    def _save_job_details(self):
        job = {}
        job['task_id'] = self.request.id
        job['inventory'] = self.params.inventory
        job['task_state'] = 'pending'
        job['result'] = 'running'
        job['playbook'] = self.params.playbook
        job['step_result'] = {}
        job['start_time'] = Time()
        job['finish_time'] = ''
        job['update_time'] = ()
        job['last_message'] = ''
        # job['last_message'] = {}
        job_store = Rds('job-' + str(job['task_id']))
        job_store.setter(job)
        log.debug(job)
        return job

    def _remove_empty_value(self, params):
        new_params = {}
        for k, v in params.items():
            if isinstance(v, dict):
                v = self._remove_empty_value(v)
            if not v in (u'', None, {}):
                new_params[k] = v
        return new_params

    def _parse_inventory(self):
        self.params.inventory = eval_json_data(self.params.inventory)
        if type(self.params.inventory) != type({}):
            raise Exception("invalid inventory format.")
        #  log.debug(self.params.inventory)
        self.params.parsed_inventory = []
        if self.params.inventory.has_key(self.LINE_INV):
            # add list inventory
            if type(self.params.inventory[self.LINE_INV]) in (type(''), type(u'')):
                self.params.parsed_inventory = self.params.inventory[self.LINE_INV] + ","
                return
            elif type(self.params.inventory[self.LINE_INV]) == type([]):
                self.params.parsed_inventory = ",".join(self.params.inventory[self.LINE_INV]) + ","
                return
        elif type(self.params.inventory) == type({}):
            # add dict inventory
            f = tempfile.NamedTemporaryFile(delete=False)
            self.params.dict_inventory = f.name
            for (host, host_list) in self.params.inventory.iteritems():
                if host == self.META_CODE:
                    continue
                f.write("[%s]\n" % host)
                if type(host_list) == type([]):
                    for i in host_list:
                        f.write("%s\n" % i)
                else:
                    f.write("%s\n" % host_list)
            f.close()
        else:
            raise Exception("invalid inventory.")

    def _build_hostvars(self):
        content = []
        f = open(self.params.dict_inventory, 'r')
        for line in f.readlines():
            line = line.strip()
            if self.params.inventory[self.META_CODE].has_key(line):
                for (k, v) in self.params.inventory[self.META_CODE][line].iteritems():
                    log.debug('-----------------')
                    log.debug(k)
                    if k=='key':
                        f = tempfile.NamedTemporaryFile(delete=False)
                        log.debug(" KEY **** %s" % v)
                        f.write(v)
                        f.close()
                        line = line + ' ' + 'ansible_ssh_private_key_file' + '=' + f.name
                    else:
                        line = line + ' ' + k + '=' + v
            content.append(line + '\n')
        f.close()
        with open(self.params.dict_inventory, 'w') as f:
            f.writelines(content)
        f.close()

    def _build_args(self):

        if self.params.dict_inventory:
            log.debug(" HIT **** %s" % self.params.dict_inventory)
            args = ["-i \'"+ self.params.dict_inventory + "\'"]
        else:
            args = ["-i \'"+ self.params.parsed_inventory + "\'"]
        args.append("-e")
        args.append("'api_job_task_id=" + self.request.id + "'")

        if self.params.inventory.has_key(self.META_CODE) and not self.params.inventory.has_key(self.LINE_INV):
            self._build_hostvars()
        elif self.params.key:
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(self.params.key)
            f.close()
            args.append("--private-key")
            args.append(f.name)
        elif self.params.username and self.params.password:
            args.append("-e")
            args.append("'ansible_ssh_user=" + self.params.username + "'")
            args.append("-e")
            args.append("'ansible_ssh_pass=" + self.params.password + "'")
        elif self.params.ssh_pey:
            log.debug("add ssh public key")
        else:
            raise Exception("invalid credential.")

        if self.params.limit:
            args.append("--limit")
            args.append(self.params.limit)
        if self.params.forks:
            args.append("--forks")
            args.append(self.params.forks)
        if self.params.variables:
            args.append("-e")
            args.append("\"" + str(convert(self.params.variables)) + "\"")
        if self.params.start_task:
            args.append("--start-at-task")
            args.append("'" + self.param.start_task+ "'")
        if self.params.private_key:
            args.append("--private-key")
            args.append(self.params.private_key)
        if self.params.tasks:
            args.append("--list-tasks")
            self.task_type = 'list_tasks'
        if self.params.tags:
            args.append("--list-tags")
            self.task_type = 'list_tags'
        log.debug(args)
        return " ".join(args)

    def _call_ansible(self):
        self._parse_inventory()
        args = self._build_args()
        log.debug("Ansible args: %s" % args)
        cmd = self._build_cmd(args)
        file_handler = self._get_file_handler()
        log.debug("Put command stdout to %s" % file_handler)
        self._run_cmd(file_handler, cmd)

    def _build_cmd(self, args):
        cmd = app.config['ANSIBLE'] + " " + args + " " \
                + get_playbook_dir(self.params.playbook) + "/site.yml"
        log.info("Ansible command: %s" % cmd)
        return cmd

    def _get_file_handler(self):
        return str(app.config['STDOUT_DIR'] + '/' + self.request.id + '.log')

    def _run_cmd(self, file_handler, cmd):
        f = open(file_handler, 'w')
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sys.stdout = f
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            sys.stdout.write(str(nextline))
            sys.stdout.flush()
        sys.stdout = sys.__stdout__
        f.close()
        f = open(file_handler, 'r')
        output = f.readlines()
        f.close()
        job_store = Rds('job-' + self.request.id)
        job = job_store.getter()
        job['task_state'] = 'finished'
        job['finish_time'] = Time()
        job['update_time'] = Time()
        job_store.setter(job)
        log.debug(job)
        return output
