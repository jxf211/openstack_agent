#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import logging
import argparse
from oslo.config import cfg
import logger
from keystone import init_keystone
from server import Server
#from router import Router
#from controller import Controller
from const import OSAGENT_CFG
import signal
from router import API 
conf_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help="The host IP to bind to"),
    cfg.IntOpt('bind_port', default=20018,
               help="The port to bind to"),
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daemon", help="run in background",
                        action="store_true")
    parser.add_argument("-g", "--debug", help="run in debug mode",
                        action="store_true")
    args = parser.parse_args()

    logger.init_logger(args)

    log.info('======== Launching OSAGENT Adapter ========')

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    if args.daemon and os.getppid() != 1:
        daemonize()

    try:
        config_init()
        init_keystone()
        #controller = Controller()
        #app = Router(controller)
        app = API()
        server = Server(app, host=conf.bind_host, port=conf.bind_port)
        server.start()
        server.wait()
    except KeyboardInterrupt as e:
        log.error(e)
        server.stop()
    except Exception as e:
        log.error(e)
