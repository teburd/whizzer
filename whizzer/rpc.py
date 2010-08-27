import marshal

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
        return self.methods[method](args, kwargs)
    
    def add(self, fn, name=None):
        """Add a method that the dispatcher will know about.

        name -- alias for the function
        fn -- a callable object

        """
        if not name:
            name = fn.__name__
        self.methods[name] = fn


class ObjectDispatch(Dispatch):
    """Object dispatch takes an object with functions marked
    using the remote decorator and sets up the dispatch to
    automatically add those.

    """
    def __init__(self, obj):
        """Instantiate a object dispatcher, takes an object
        with methods marked using the remote decorator

        """
        Dispatch.__init__(self)
        self.obj = obj
        attrs = dir(self.obj)
        for attr in attrs:
            a = getattr(self.obj, attr)
            if hasattr(a, 'remote'):
                self.add(a, a.remote['name'])

class RPCProtocol(object):
    def __init__(self, loop, dispatch):
        LengthProtocol.__init__(self, loop)
        self.dispatch = dispatch

    def message(self, message):
        """Handle a message by decoding it in to arguments the dispatcher understands."""

    def proxy(self):
        """Return a proxy object."""


class MarshalRPCProtocol(object):
    pass

class JSONRPCProtocol(object):
    pass

class RPCClient(object):
    """A general RPC client."""
