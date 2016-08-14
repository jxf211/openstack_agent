import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler


class LcTimedRotatingFileHandler(TimedRotatingFileHandler):

    def __init__(self, *args, **kwargs):
        TimedRotatingFileHandler.__init__(self, *args, **kwargs)
        # redirect stderr to log file
        os.dup2(self.stream.fileno(), sys.stderr.fileno())

    def doRollover(self):
        TimedRotatingFileHandler.doRollover(self)
        # redirect stderr to log file
        os.dup2(self.stream.fileno(), sys.stderr.fileno())


def init_logger(args=None):
    handler = LcTimedRotatingFileHandler(
        '/var/log/osagent.log', when='midnight')
    #handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s T%(thread)d-%(threadName)s '
                                  '%(levelname)s %(module)s.'
                                  '%(funcName)s.%(lineno)d: %(message)s')
    handler.setFormatter(formatter)

    _log_levels = {
        'keystone': logging.DEBUG,
        'server': logging.DEBUG,
        'router': logging.DEBUG,
        'host': logging.DEBUG,
        'neutron': logging.DEBUG,
        'nova': logging.DEBUG,
        'info': logging.DEBUG,
        'controller': logging.DEBUG,
        'http': logging.DEBUG,
        'heat': logging.DEBUG,
        'glance': logging.DEBUG,
        'exception':logging.DEBUG,
        'serializers':logging.DEBUG,
        '__main__': logging.DEBUG,
    }
    for logger, level in _log_levels.items():
        log = logging.getLogger(logger)
        log.setLevel(level)
        log.addHandler(handler)
