#!/usr/bin/env python

"""
  Copyright notice
  ================

  Copyright (C) 2018
      Julian Gruendner    <juliangruendner@googlemail.com>

"""

import sys
import getopt
import http.client
import threading
import sys
sys.path.append('../ds_common')
from ds_poll_util import PollState
from ds_pollworker import Pollworker

def show_help():
    print("""\
Syntax: python %s <options>
 -a <addr>         listen address (default 0.0.0.0)
 -d <filename>     on termination, dump requests & responses to file
 -h                show this help screen
 -q <host:[port]>  full address of queue (default = 8)
 -o <host:[port]>  full address of opal server
 -v                be more verbose
 -t <number>       number of threads to create for polling
""" % sys.argv[0])

def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:d:hp:r:vq:o:st:")
    except getopt.GetoptError as e:
        print(str(e))
        show_help()
        exit(1)

    opts = dict([(k.lstrip('-'), v) for (k, v) in opts])

    if 'h' in opts:
        show_help()
        exit(0)

    ps = PollState()

    if 'v' in opts:
        ps.log.verbosity += 1

    if 'd' in opts:
        ps.dumpfile = opts['d']

    if 'a' in opts:
        ps.listenaddr = opts['a']

    # Check and parse queue host
    if 'q' in opts:
        h = opts['q']
        if ':' not in h:
            p = 8001
        else:
            h, p = h.split(':')
            p = int(p)
        ps.q_addr = (h, p)

    # Check and parse redirection host
    if 'o' in opts:
        h = opts['o']
        if ':' not in h:
            p = 8880
        else:
            h, p = h.split(':')
            p = int(p)
        ps.opal_addr = (h, p)

    ps.https = True if 's' in opts else False

    ps.n_threads = 2
    if 't' in opts:
        ps.n_threads = opts['t']

    return ps

def pollworker_exec(threadName, pollstate):
    print(threadName, file=sys.stderr)

    q_host, q_port = pollstate.q_addr
    o_host, o_port = pollstate.opal_addr

    pollworker = Pollworker(q_host, q_port, o_host, o_port, pollstate, threadName)

    while(True):
        req = pollworker.getNextRequest()


def main():
    global pollstate
    pollstate = parse_options()
    threads = []
    try:
        for i in range(0, int(pollstate.n_threads)):
            t = threading.Thread(target=pollworker_exec, args=("Thread-" + str(i), pollstate))
            threads.append(t)
            t.start()
    except Exception as e:
        pollstate.log.error(e.__str__() + ": Error on starting poll threads")
    while threading.active_count() > 1:
        pass


if __name__ == "__main__":
    global pollstate
    try:
        main()
    except KeyboardInterrupt as e:
        pollstate.log.info("Terminating... ")
