#!/usr/bin/env python
# encoding: utf-8


import os
from .. import app


def get_inventories_dir(playbook_name):
    return get_real_dir(os.path.join(get_playbook_dir(playbook_name), "inventories"))


def get_real_dir(f):
    return os.path.realpath(f)


def get_playbook_dir(playbook_name):
    return get_real_dir(os.path.join(app.config['ANSIBLE_PLAYBOOK_ROOT'], playbook_name))


def get_playbooks_dir():
    playbooks_dir = []
    for dirName, subdirList, fileList in os.walk(app.config['ANSIBLE_PLAYBOOK_ROOT']):
        depth = dirName.count(os.path.sep) - app.config['ANSIBLE_PLAYBOOK_ROOT'].count(os.path.sep)
        if depth == 0:
            playbooks_dir.append(subdirList)
    return playbooks_dir
