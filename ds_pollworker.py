"""
  Copyright notice
  ================
  
  Copyright (C) 2018
      Julian Gruendner   <juliangruendner@googlemail.com>
      License: GNU, see LICENSE for more details.
  
"""

import io
import http.client
import ssl
import sys
from ds_http.ds_http import HTTPRequest, HTTPResponse

class Pollworker():

    def __init__(self, q_host, q_port, o_host, o_port, pollstate, threadName):
        self.q_host = q_host
        self.q_port = q_port
        self.o_host = o_host
        self.o_port = o_port
        self.pollstate = pollstate
        self.threadName = threadName

    def createConnection(self, host, port):

        try:
            if self.pollstate.https:
                defContext = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(host, port, context=defContext)
                # cafile = "/Users/juliangruendner/phd/code/ds_develop/ds_queue/cert/ncerts/test.crt"
                # defContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=cafile)
                # conn = http.client.HTTPSConnection(host, port, context=defContext)
            else:
                # HTTP Connection
                conn = http.client.HTTPConnection(host, port)
        except Exception as e:
            print(e, file=sys.stderr)
            self.pollstate.log.debug(e.__str__())

        self._host = host
        self._port = port

        return conn

    def _request(self, conn, method, path, params, headers):
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for header, v in headers.items():
            if header.lower() == 'content-length':
                conn.putheader(header, str(len(params)))
            else:
                for i in v:
                    conn.putheader(header, i)
        conn.endheaders()

        if len(params) > 0:
            conn.send(params.encode('latin-1'))

    def _getresponse(self, conn):
        try:
            res = conn.getresponse()
        except http.client.HTTPException as e:
            self.pollstate.log.debug(e.__str__() + ": Error getting response")
            return None

        body = res.read()
        if res.version == 10:
            proto = "HTTP/1.0"
        else:
            proto = "HTTP/1.1"

        code = res.status
        msg = res.reason
        headers = res.getheaders()
        headers = dict((x, y) for x, y in headers)
        res = HTTPResponse(proto, code, msg, headers, body)

        if 'Transfer-Encoding' in headers.keys():
            res.removeHeader('Transfer-Encoding')
            res.addHeader('Content-Length', str(len(body)))

        return res

    def _getresponse_with_body_as_string(self, conn):
        try:
            res = conn.getresponse()
        except http.client.HTTPException as e:
            self.pollstate.log.debug(e.__str__() + ": Error getting response")
            return None

        body = res.read()
        body = body.decode('latin-1')  # add body decoding to convert to bytes

        if res.version == 10:
            proto = "HTTP/1.0"
        else:
            proto = "HTTP/1.1"

        code = res.status
        msg = res.reason
        headers = res.getheaders()
        headers = dict((x, y) for x, y in headers)
        res = HTTPResponse(proto, code, msg, headers, body)

        if 'Transfer-Encoding' in headers.keys():
            res.removeHeader('Transfer-Encoding')
            res.addHeader('Content-Length', str(len(body)))

        return res

    def getNextRequest(self):

        q_conn = self.createConnection(self.q_host, self.q_port)
        q_conn.request("GET", "/?getQueuedRequest=True")
        res = self._getresponse(q_conn)
        return res

    def handleRequest(self, res):

        if res.code == 204:
            return

        res_buf = io.BytesIO(res.body)
        req = HTTPRequest.build(res_buf)

        # get Uuid to add to response and remove from request
        reqId = req.getHeader('reqId')[0]
        req.removeHeader('reqId')

        # self.pollstate.log.log_message_line(req)
        self.pollstate.log.log_message_as_json(req)

        opal_conn = self.createConnection(self.o_host, self.o_port)
        self._request(opal_conn, req.getMethod(), req.getPath(), req.getBody(), req.headers)

        res = self._getresponse_with_body_as_string(opal_conn)

        q_conn = self.createConnection(self.q_host, self.q_port)
        q_conn.request("POST", "/?setQueuedResponse=True&reqId=" + reqId, res.serialize())
