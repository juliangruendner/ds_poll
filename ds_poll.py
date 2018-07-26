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
import httplib

import sys
sys.path.append('../ds_common')
from ds_poll_util import *
from ds_pollworker import *

def show_help():
    print """\
Syntax: python %s <options>
 -a <addr>         listen address (default 0.0.0.0)
 -d <filename>     on termination, dump requests & responses to file
 -h                show this help screen
 -q <host:[port]>  full address of queue (default = 8)
 -o <host:[port]>  full address of opal server
 -v                be more verbose
 -x <filename>     load a ProxPy plugin
""" % sys.argv[0]

def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:d:hp:r:vx:")
    except getopt.GetoptError, e:
        print str(e)
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
        h = opts['r']
        if ':' not in h:
            p = 8880
        else:
            h,p = h.split(':')
            p = int(p)
        ps.opal_addr = (h, p)

    # Load an external plugin
    if 'x' in opts:
        ps.plugin = PollPlugin(opts['x'])

    return ps


def main():
    global pollstate
    pollstate = parse_options()
    
    q_host, q_port = pollstate.q_addr
    o_host, o_port = pollstate.opal_addr

    pollworker = Pollworker(q_host, q_port, o_host, o_port)

    while(True):
        req = pollworker.getNextRequest()



if __name__ == "__main__":
    global pollstate
    try:
        main()
    except KeyboardInterrupt, e:
        nreq, nres = pollstate.history.count()
        pollstate.log.info("Terminating... [%d requests, %d responses]" % (nreq, nres))
        if pollstate.dumpfile is not None:
            data = pollstate.history.dumpXML()
            f = open(pollstate.dumpfile, 'w')
            f.write(data)
            f.close()


