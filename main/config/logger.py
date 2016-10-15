#!/usr/bin/env python
# encoding: utf-8

import logging


class Log(object):
    @staticmethod
    def getLogger(class_name):
        logger = logging.getLogger(class_name)
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        fh = logging.FileHandler('kree2.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.propagate = False
        return logger
