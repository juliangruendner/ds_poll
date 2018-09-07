"""
  Copyright notice
  ================
  
  Copyright (C) 2018
      Julian Gruendner     <julian.gruendner@fau.de>
  
"""

import os, sys
import threading
import logging
import json
from ds_http import *
from ds_https import *
from time import gmtime, localtime, strftime

COLOR_RED    = 31
COLOR_GREEN  = 32
COLOR_YELLOW = 33
COLOR_BLUE   = 34
COLOR_PURPLE = 35

def colorize(s, color = COLOR_RED):
    return (chr(0x1B) + "[0;%dm" % color + str(s) + chr(0x1B) + "[0m")

class PollLogger:
    def __init__(self, verbosity = 0, logfile = 'allLog.log', logdir=None):
        self.verbosity = verbosity

        if not logdir:
            logdir = os.getcwd()
        
        self.logdir = logdir
        self.logfile = logfile
        self.separator = "|"

    def __out(self, msg, head, color):
        tid = threading.current_thread().ident & 0xffffffff
        tid = " %s " % colorize("<%.8x>" % tid, COLOR_PURPLE)
        print(colorize(head, color) + tid + msg)    

    def info(self, msg):
        self.__out(msg, "[*]", COLOR_GREEN)

    def warning(self, msg):
        self.__out(msg, "[#]", COLOR_YELLOW)

    def error(self, msg):
        self.__out(msg, "[!]", COLOR_RED)

    def debug(self, msg):
        if self.verbosity > 0:
            self.__out(msg, "[D]", COLOR_BLUE)

    def printMessages (self, req):
        if self.verbosity > 0:

            if not req.isResponse():
                print("#########REQUEST##########\n")
            else:
                print("=========RESPONSE=========")

            print(req)
            
            if req.body:
                print("----------body---------")
                print(req.body)
                print("----------body---------\n")
                print("----------------END---------------\n")

    
    
    def getLogfileName(self):
        time = strftime("%Y-%m-%d", localtime())
        logfile = time + "_poll.log"
        return logfile



    def log_message_line(self, html_message):
        message = ""
        
        time = strftime("%Y-%m-%d %H:%M:%S", localtime())
        req_line = "%s %s %s" % (html_message.method, html_message.url, html_message.proto)
        
        auth_header = html_message.getHeader('authorization')[0].split(" ")[1]
        decoded_auth_string = str(base64.b64decode(auth_header),'latin-1')
        user = decoded_auth_string.split(":")[0]
        body = html_message.getBody()

        message = time  + self.separator + req_line + self.separator + user + self.separator + body + self.separator
        self.write_to_log(message)
    

    def log_message_as_json(self, html_message):

        time = strftime("%Y-%m-%d %H:%M:%S", localtime())
        req_line = "%s %s %s" % (html_message.method, html_message.url, html_message.proto)
        
        auth_header = html_message.getHeader('authorization')[0].split(" ")[1]
        decoded_auth_string = str(base64.b64decode(auth_header),'latin-1')
        user = decoded_auth_string.split(":")[0]
        body = html_message.getBody()

        my_message_dict = {"time" : time, "req_line" : req_line, "user" : user, "body": body}
        self.write_to_log(json.dumps(my_message_dict))


    def write_to_log(self, message):
        logfile = self.getLogfileName()

        logging.basicConfig(filename=self.logdir + "/logging/" + logfile,level=logging.INFO)
        logging.info(message)
        

