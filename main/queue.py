#!/usr/bin/env python
# encoding: utf-8

import json
from redis import StrictRedis
from config.logger import Log

redis_kwargs = {}
broker_url = 'localhost:6379'
broker_host = broker_url
broker_host = broker_host.split('/')[0]
if ':' in broker_host:
    broker_host, broker_port = broker_host.split(':')
    redis_kwargs['port'] = int(broker_port)
redis = StrictRedis(broker_host, **redis_kwargs)
logger = Log.getLogger(__name__)


class FifoQueue(object):
    """An abstraction class implemented for a simple push/pull queue.

    Intended to allow alteration of backend details in a single, consistent
    way throughout the Tower application.
    """

    def __init__(self, queue_name):
        """Instantiate a queue object, which is able to interact with a
        particular queue.
        """
        self._queue_name = queue_name

    def __len__(self):
        """Return the length of the Redis list."""
        return redis.llen(self._queue_name)

    def push(self, value):
        """Push a value onto the right side of the queue."""
        redis.rpush(self._queue_name, json.dumps(value))

    def pop(self):
        """Retrieve a value from the left side of the queue."""
        answer = redis.lpop(self._queue_name)
        if answer:
            return json.loads(answer)


class PrimaryKey(object):
    """A self increment class abstract
    """

    def __init__(self, key_name):
        self._key_name = key_name
        if not redis.exists(self._key_name):
            redis.set(self._key_name, 0)
            redis.persist(self._key_name)
            logger.debug("PK %s initialed." % self._key_name)
        else:
            logger.debug("PK %s continue from %s" % (self._key_name, self.getter()))

    def getter(self):
        answer = redis.get(self._key_name)
        return json.loads(answer)

    def setter(self):
        redis.incr(self._key_name, 1)


class Rds(object):
    """A relational data store which store data with JSON
    """

    def __init__(self, key_name):
        self._key_name = key_name
        if not redis.exists(self._key_name):
            redis.set(self._key_name, None)
            redis.persist(self._key_name)
            logger.debug("Datastore %s initialed." % self._key_name)
        else:
            logger.debug("Datastore %s connected." % self._key_name)

    def getter(self):
        logger.debug("Datastore %s ." % self._key_name)
        #  answer = (redis.get(self._key_name))
        answer = json.loads(redis.get(self._key_name))
        return answer

    def setter(self, data):
        redis.set(self._key_name, json.dumps(data))
