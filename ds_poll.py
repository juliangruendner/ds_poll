#!/usr/bin/env python

"""
  Copyright notice
  ================
  
  Copyright (C) 2011
      Roberto Paleari     <roberto.paleari@gmail.com>
      Alessandro Reina    <alessandro.reina@gmail.com>
  
  This program is free software: you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.
  
  HyperDbg is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License along with
  this program. If not, see <http://www.gnu.org/licenses/>.
  
"""

import sys
import getopt
import http.client
import threading
import sys
sys.path.append('../ds_common')

from ds_poll_util import *
from ds_pollworker import *

def show_help():
    print("""\
Syntax: python %s <options>
 -a <addr>         listen address (default 0.0.0.0)
 -d <filename>     on termination, dump requests & responses to file
 -h                show this help screen
 -q <host:[port]>  full address of queue (default = 8)
 -o <host:[port]>  full address of opal server
 -v                be more verbose
 -x <filename>     load a ProxPy plugin
 -t <number>       number of threads to create for polling
""" % sys.argv[0])

def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:d:hp:r:vx:q:o:st:")
    except getopt.GetoptError as e:
        print(str(e))
        show_help()
        exit(1)

    opts = dict([(k.lstrip('-'), v) for (k,v) in opts])

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
            h,p = h.split(':')
            p = int(p)
        ps.q_addr = (h, p)
    
    # Check and parse redirection host
    if 'o' in opts:
        h = opts['o']
        if ':' not in h:
            p = 8880
        else:
            h,p = h.split(':')
            p = int(p)
        ps.opal_addr = (h, p)

    ps.https = True if 's' in opts else False

    # Load an external plugin
    if 'x' in opts:
        ps.plugin = PollPlugin(opts['x'])

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
        for i in range(0,int(pollstate.n_threads)):
            t = threading.Thread(target=pollworker_exec, args=("Thread-" + str(i), pollstate))
            threads.append(t)
            t.start()
    except:
        print ("Error: unable to start threads", file=sys.stderr)
    while threading.active_count() > 1:
        pass

if __name__ == "__main__":
    global pollstate
    try:
        main()
    except KeyboardInterrupt as e:
        nreq, nres = pollstate.history.count()
        pollstate.log.info("Terminating... [%d requests, %d responses]" % (nreq, nres))
        '''if pollstate.dumpfile is not None:
            data = pollstate.history.dumpXML()
            f = open(pollstate.dumpfile, 'w')
            f.write(data)
            f.close()'''


