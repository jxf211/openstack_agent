#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import logging
import argparse
from oslo.config import cfg
import logger
from keystone import init_keystone
#from server import Server
from const import OSAGENT_CFG
import signal
from router import API
import wsgiserver

conf_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help="The host IP to bind to"),
    cfg.IntOpt('bind_port', default=20018,
               help="The port to bind to"),
    ]

common_cli_opts = [
    cfg.BoolOpt('daemon',
                short='d',
                default=False,
                help='run in background'),
    cfg.BoolOpt('debug',
                short='g',
                default=False,
                help='run in debug mode'),
    ]

conf = cfg.CONF
log = logging.getLogger(__name__)

def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    """
    do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

def config_init():
    """
    load cfg
    """
    conf.register_opts(conf_opts)
    conf.register_cli_opts(common_cli_opts)
    conf(default_config_files=[OSAGENT_CFG])
    if not conf.config_file:
        sys.exit(1)

def signal_handler(sig, frame):
    if sig == signal.SIGTERM:
        log.info("Terminating  osagent...")
    if sig == signal.SIGHUP:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        log.info("ignore SIGHUP.... ")

if __name__ == '__main__':
    config_init()
    logger.init_logger(conf)
    log.info('======== Launching OSAGENT Adapter ========')
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    if conf.daemon and os.getppid() != 1:
        daemonize()
    try:
        init_keystone()
        app = API()

        port = conf.agent_api.bind_port
        host = conf.agent_api.bind_host
        log.info(('Starting OpenStack Agent REST API on %(host)s:%(port)s'),
                         {'host': host, 'port': port})

        server = wsgiserver.Server('agent_api', conf.agent_api)
        server.start(app, default_port=port)
        server.wait()
    except KeyboardInterrupt as e:
        log.error(e)
        server.stop()
    except Exception as e:
        log.error(e)
