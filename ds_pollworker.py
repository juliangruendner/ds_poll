from ds_http import *
from ds_https import *
import io
import http.client
import ssl

class Pollworker():

    def __init__(self, q_host, q_port, o_host, o_port, pollstate):
        print("initiating worker")
        self.target = None
        self.keepalive = False

        self.q_host = q_host
        self.q_port = q_port
        self.o_host = o_host
        self.o_port = o_port
        self.pollstate = pollstate

    def createConnection(self, host, port):
        
        if self.target and self._host == host:
            return self.target

        try:
            # If a SSL tunnel was established, create a HTTPS connection to the server
            if self.pollstate.https:
                # FIXME - change to verify context
                defContext = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(host, port, context=defContext)
            else:
                # HTTP Connection
                conn = http.client.HTTPConnection(host, port)
        except Exception as e:
            self.pollstate.log.debug(e.__str__())

        # If we need a persistent connection, add the socket to the dictionary
        if self.keepalive:
            self.target = conn

        self._host = host
        self._port = port
            
        return conn
    
    # get next request from queue server

    def _request(self, conn, method, path, params, headers):
        conn.putrequest(method, path, skip_host = True, skip_accept_encoding = True)
        for header,v in headers.items():
            # auto-fix content-length
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
            # FIXME: check the return value into the do* methods
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

    def _getresponse2(self, conn):
        try:
            res = conn.getresponse()
        except http.client.HTTPException as e:
            self.pollstate.log.debug(e.__str__() + ": Error getting response")
            # FIXME: check the return value into the do* methods
            return None

        body = res.read()
        body = body.decode('latin-1')

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
        q_conn.request("GET","/?getQueuedRequest=True")
        res = self._getresponse(q_conn)

        res_buf = io.BytesIO(res.body)
        req = HTTPRequest.build(res_buf)

        #self.pollstate.log.log_message_line(req)
        self.pollstate.log.log_message_as_json(req)

        opal_conn = self.createConnection(self.o_host, self.o_port)
        self._request(opal_conn, req.getMethod(), req.getPath(), req.getBody(), req.headers)
        
        res = self._getresponse2(opal_conn)
        q_conn = self.createConnection(self.q_host, self.q_port)
        q_conn.request("POST", "/?setQueuedResponse=True", res.serialize())






