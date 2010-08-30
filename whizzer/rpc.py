import marshal
from .protocols import LengthProtocol
from .protocol import ProtocolFactory
from .futures import Future

class RPCError(Exception):
    pass

class Dispatch(object):
    """Basic method dispatcher."""

    def __init__(self):
        """Instantiate a basic dispatcher."""
        self.methods = dict()

    def call(self, method, *args, **kwargs):
        """Call a method given some args and kwargs.

        method -- string containing the method name to call
        args -- arguments
        kwargs -- key word arguments

        returns the result of the method.

        May raise an exception if the method isn't in the dict.

        """
        print(method + str(args)+str(kwargs))
        return self.methods[method](*args, **kwargs)
    
    def add(self, fn, name=None):
        """Add a method that the dispatcher will know about.

        name -- alias for the function
        fn -- a callable object

        """
        if not name:
            name = fn.__name__
        self.methods[name] = fn

def remote(fn, name=None, types=None):
    """Decorator that adds a remote attribute to a function.
    
    fn -- function being decorated
    name -- aliased name of the function, used for remote proxies
    types -- a argument type specifier, can be used to ensure
             arguments are of the correct type
    """
    if not name:
        name = fn.__name__
    fn.remote = {"name":name, "types":types}
    return fn

class ObjectDispatch(Dispatch):
    """Object dispatch takes an object with functions marked
    using the remote decorator and sets up the dispatch to
    automatically add those.

    """
    def __init__(self, obj):
        """Instantiate a object dispatcher, takes an object
        with methods marked using the remote decorator

        obj -- Object with methods decorated by the remote decorator.

        """
        Dispatch.__init__(self)
        self.obj = obj
        attrs = dir(self.obj)
        for attr in attrs:
            a = getattr(self.obj, attr)
            if hasattr(a, 'remote'):
                self.add(a, a.remote['name'])

class Proxy(object):
    def set_timeout(self, timeout):
        """Set a timeout for all synchronous calls, by default there is none."""
    
    def call(self, timeout, method, *args, **kwargs):
        """Perform a synchronous remote call where the returned value is given immediately.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        Any exceptions the remote call raised that can be sent over the wire are raised.

        Internally this calls begin_call(method, *args, **kwargs).result(timeout=self.timeout)

        """

    def notify(self, method, *args, **kwargs):
        """Perform a synchronous remote call where value no return value is desired.

        While faster than call it still blocks until the remote callback has been sent.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        """

    def begin_call(self, method, *args, **kwargs):
        """Perform an asynchronous remote call where the return value is not known yet.

        This returns immediately with a Future object. The future object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        """

    def begin_notify(self, method, *args, **kwargs):
        """Perform an asynchronous remote call where no return value is expected.

        This returns immediately with a Future object. The future object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        The Future object's result is set to None when the notify message has been sent.

        """

class MarshalRPCProxy(Proxy):
    def __init__(self, loop, protocol):
        self.loop = loop
        self.protocol = protocol
        self.calls = set()
        self.request_num = 0
        self.requests = dict()
        self.timeout = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def call(self, method, *args, **kwargs):
        """Perform a synchronous remote call where the returned value is given immediately.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        Any exceptions the remote call raised that can be sent over the wire are raised.

        Internally this calls begin_call(method, *args, **kwargs).result(timeout=self.timeout)

        """
        return self.begin_call(method, *args, **kwargs).result(self.timeout)

    def notify(self, timeout, method, *args, **kwargs):
        """Perform a synchronous remote call where value no return value is desired.

        While faster than call it still blocks until the remote callback has been sent.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        """
        return self.begin_notify(method, *args, **kwargs).result(timeout)

    def begin_call(self, method, *args, **kwargs):
        """Perform an asynchronous remote call where the return value is not known yet.

        This returns immediately with a Future object. The future object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        """
        f = Future(self.loop)
        f.request = self.request_num
        self.request_num += 1
        self.requests[f.request] = f
        print "sending " + str(args)
        msg = marshal.dumps((False, f.request, method, args, kwargs))
        self.protocol.send(msg)
        return f

    def begin_notify(self, method, *args, **kwargs):
        """Perform an asynchronous remote call where no return value is expected.

        This returns immediately with a Future object. The future object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        The Future object's result is set to None when the notify message has been sent.

        """
        f = Future(self.loop)
        f.request = self.request_num
        self.request_num += 1
        msg = marshal.dumps((False, f.request, method, args, kwargs))
        self.protocol.send(msg)
        f.set_result(None)
        return f

    def results(self, msg):
        """Handle a results message given to the proxy by the protocol object."""
        isresult, iserror, request, result = msg
        if not iserror:
            self.requests[request].set_result(result)
        else:
            self.requests[request].set_exception(RPCException(result))
        del self.requests[request]


class MarshalRPCProtocol(LengthProtocol):
    def __init__(self, loop, factory, dispatch=Dispatch()):
        LengthProtocol.__init__(self, loop)
        self.factory = factory
        self.dispatch = dispatch
        self._proxy = None
        self._proxy_futures = []

    def connection_made(self):
        """When a connection is made the proxy is available."""
        self._proxy = MarshalRPCProxy(self.loop, self)
        for f in self._proxy_futures:
            f.set_result(self._proxy)

    def message(self, message):
        """Handle an incoming message (remote call request)."""
        msg = marshal.loads(message)
        print msg
        if msg[0]: # result flag set to be true
            self._proxy.results(msg) 
        else:
            resultflag, request, method, args, kwargs = msg 

            result = None
            iserror = False
            try:
                result = self.dispatch.call(method, args, kwargs)
            except RPCError as e:
                iserror = True
                result = e

            if isinstance(result, Future):
                future.request = request
                future.add_done_callback(self._result.done)
            else:
                self._send_results(request, iserror, result)

    def _result_done(self, future):
        """This is set as the done callback of a dispatched call that returns a future."""
        if future.exception():
            self._send_results(future.request, True, future.exception())
        else:
            self._send_results(future.request, False, future.result())

    def _send_results(self, request, iserror, results):
        if iserror:
            results = marshal.dumps(True, request, results, None)
        else:
            results = marshal.dumps(True, request, None, results)
        self.send(results)

    def proxy(self):
        """Return a Future that will result in a proxy object in the future."""
        f = Future(self.loop)
        self._proxy_futures.append(f)

        if self._proxy:
            f.set_result(self._proxy)

        return f

    def connection_lost(self, reason=None):
        """Tell the factory we lost our connection."""
        self.factory.lost_connection(self)
        self.factory = None

class RPCProtocolFactory(ProtocolFactory):
    def __init__(self, loop, dispatch=Dispatch()):
        ProtocolFactory.__init__(self, loop)
        self.dispatch = dispatch
        self.protocol = None
        self.protocols = []

    def proxy(self, conn_number):
        """Return a proxy for a given connection number."""
        return self.protocols[conn_number].proxy()

    def build(self):
        p = self.protocol(self.loop, self, self.dispatch)
        self.protocols.append(p)
        return p

    def lost_connection(self, p):
        """Called by the rpc protocol whenever it loses a connection."""
        self.protocols.remove(p)

class JSONRPCProtocol(object):
    pass

