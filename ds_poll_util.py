from logger import Logger

class PollState:
    def __init__(self, q_addr = ('localhost' ,8001), opal_addr = ('localhost', 8880)):
        # Configuration options, set to default values
        self.plugin     = PollPlugin()
        self.dumpfile   = None
        self.q_addr = q_addr
        self.opal_addr = opal_addr

        # Internal state
        self.log        = Logger()
        self.history    = '' #HttpHistory()
        
        
    @staticmethod
    def getTargetHost(req):
        global pollstate
        # Determine the target host (check if redirection is in place)
        if pollstate.redirect is None:
            target = req.getHost()
        else:
            target = proxystate.redirect

        return target

class PollPlugin:
    EVENT_MANGLE_REQUEST  = 1
    EVENT_MANGLE_RESPONSE = 2

    __DISPATCH_MAP = {
        EVENT_MANGLE_REQUEST:  'proxy_mangle_request',
        EVENT_MANGLE_RESPONSE: 'proxy_mangle_response',
        }

    def __init__(self, filename = None):
        self.filename = filename
    
        if filename is not None:
            import imp
            assert os.path.isfile(filename)
            self.module = imp.load_source('plugin', self.filename)
        else:
            self.module = None

    def dispatch(self, event, *args):
        if self.module is None:
            # No plugin
            return None

        assert event in ProxyPlugin.__DISPATCH_MAP
        try:
            a = getattr(self.module, ProxyPlugin.__DISPATCH_MAP[event])
        except AttributeError:
            a = None

        if a is not None:
            r = a(*args)
        else:
            r = None
            
        return r

    @staticmethod
    def delegate(event, arg):
        global proxystate

        # Allocate a history entry
        hid = proxystate.history.allocate()

        if event == ProxyPlugin.EVENT_MANGLE_REQUEST:
            proxystate.history[hid].setOriginalRequest(arg)
            # Process this argument through the plugin
            mangled_arg = proxystate.plugin.dispatch(ProxyPlugin.EVENT_MANGLE_REQUEST, arg.clone())

        elif event == ProxyPlugin.EVENT_MANGLE_RESPONSE:
            proxystate.history[hid].setOriginalResponse(arg)

            # Process this argument through the plugin
            mangled_arg = proxystate.plugin.dispatch(ProxyPlugin.EVENT_MANGLE_RESPONSE, arg.clone())

        if mangled_arg is not None:
            if event == ProxyPlugin.EVENT_MANGLE_REQUEST:
                proxystate.history[hid].setMangledRequest(mangled_arg)
            elif event == ProxyPlugin.EVENT_MANGLE_RESPONSE:
                proxystate.history[hid].setMangledResponse(mangled_arg)

            # HTTPConnection.request does the dirty work :-)
            ret = mangled_arg
        else:
            # No plugin is currently installed, or the plugin does not define
            # the proper method, or it returned None. We fall back on the
            # original argument
            ret = arg

        return ret
