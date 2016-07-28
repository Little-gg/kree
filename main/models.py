#!/usr/bin/env python
# encoding: utf-8


from path_utils import *
from tasks import invoke, check_task_result
from tempfile import NamedTemporaryFile
from . import logger
from . import app
import ast
import re
import json


class Task(object):
    def __init__(self, task_id):
        self.task_id = task_id

    def get_task_detail(self):
        result, state = check_task_result(self.task_id)
        return result, state


class NullJob(object):
    def available_playbooks(self):
        return get_playbooks_dir()


class NoParamJob(NullJob):
    def __init__(self, name):
        self.name = name

    def path(self):
        return get_playbook_dir(self.name)

    def get_detail(self):
        try:
            f = open("%s/README.md" % self.path(), 'r')
            detail = f.read().splitlines()
            f.close()
            return detail
        except:
            return 'Open readme failed!'

    def available_methods(self):
        methods = []
        method_path = get_playbook_dir(self.name)
        for dirpath,dirnames,filenames in os.walk(method_path.encode('utf-8')):
            depth = dirpath.count(os.path.sep) - app.config['ANSIBLE_PLAYBOOK_ROOT'].count(os.path.sep)
            if depth == 1:
                for file in filenames:
                    if re.search('.yml$', file):
                        methods.append(file)
        return methods


class Job(NoParamJob):
    def __init__(self, name, params):
        self.params = params
        self.name = name
        self.stream_file = NamedTemporaryFile().name


    @property
    def tags(self):
        return self.params.tags if self.params.tags else False

    @property
    def tasks(self):
        return self.params.tasks if self.params.tasks else False

    @property
    def limit(self):
        return self.params.limit if self.params.limit else False

    @property
    def forks(self):
        return self.params.forks if self.params.forks else False

    @property
    def variables(self):
        return self.params.variables if self.params.variables else False

    @property
    def private_key(self):
        return self.params.private_key if self.params.private_key else False

    @property
    def method(self):
        return self.params.method

    @property
    def username(self):
        return self.params.username if self.params.username else 'root'

    @property
    def password(self):
        return self.params.password if self.params.password else ''

    @property
    def inventory(self):
        inventories = []
        if not self.params.inventory:
            inventory_path= get_inventories_dir(self.name)
            if os.path.exists(inventory_path):
                for dirpath,dirnames,filenames in os.walk(inventory_path.encode('utf-8')):
                    for filename in filenames:
                        inventory = os.path.join(dirpath,filename)
                        inventory = os.path.relpath(inventory, inventory_path)
                        inventories.append(inventory)
            return inventories[0]
        else:
            inventory = ast.literal_eval(json.dumps(self.params.inventory))
            return self._generate_inventory(inventory)

    def _generate_inventory(self, inventory):
        logger.info("Generate inventory CALLed!")
        logger.info("Inventory %s" % inventory)
        inv_file = NamedTemporaryFile().name
        print inv_file
        f = open(inv_file, 'w')
        for k, v in inventory.iteritems():
            f.writelines('[' + k + ']\n')
            if self.username and self.password:
                f.writelines(v + ' ')
                f.writelines('ansible_ssh_user=%s ' % self.username)
                f.writelines('ansible_ssh_pass=%s\n' % self.password)
            else:
                f.writelines(v + ' ')
                f.writelines('ansible_ssh_user=%s\n' % self.username)
        f.close()
        return str(inv_file)

    def validate_playbook_existance(self):
        if self.name:
            playbook_path = get_playbook_dir(self.name)
            if os.path.exists(playbook_path):
                return True
            else:
                return False

    def run(self, method):
        cmd = self.build_cmd(self.build_args(), method)
        logger.info("Ansible command: %s" % cmd)
        task_id, task_state = invoke(self, cmd)
        return task_id, task_state

    def build_args(self):
        if not self.params.inventory:
            args = ['-i', get_inventories_dir(self.name)+ "/" + self.inventory]
        else:
            args = ['-i', self.inventory]
        if self.limit:
            args.append("--limit")
            args.append(self.limit)
        if self.forks:
            args.append("--forks")
            args.append(self.forks)
        if self.variables:
            args.append("-e")
            args.append("'" + self.variables + "'")
        if self.private_key:
            args.append("--private-key")
            args.append(self.private_key)
        if self.tasks:
            args.append("--list-tasks")
        if self.tags:
            args.append("--list-tags")
        return " ".join(args)

    def build_cmd(self, args, method):
        cmd = app.config['ANSIBLE'] + " " + args + " " \
                + get_playbook_dir(self.name) + "/" + method
        return cmd
