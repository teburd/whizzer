# -*- coding: utf-8 -*-
# Copyright (c) 2010 Tom Burdick <thomas.burdick@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


try:
    import cPickle as pickle
except:
    import pickle

import struct

import logbook

from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.defer import Deferred

from whizzer.rpc.proxy import Proxy
from whizzer.rpc.dispatch import Dispatch

logger = logbook.Logger(__name__)


def dumps(obj):
    return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

def loads(string):
    return pickle.loads(string)


class PickleProxy(Proxy):
    """A MessagePack-RPC Proxy."""

    def __init__(self, loop, protocol):
        """PickleProxy

        loop -- A pyev loop.
        protocol -- An instance of PickleProtocol.

        """
        self.loop = loop
        self.protocol = protocol
        self.request_num = 0
        self.requests = dict()
        self.timeout = None

    def set_timeout(self, timeout):
        """Set the timeout of blocking calls, None means block forever.

        timeout -- seconds after which to raise a TimeoutError for blocking calls.

        """
        self.timeout = timeout

    def call(self, method, *args, **kwargs):
        """Perform a synchronous remote call where the returned value is given immediately.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        Any exceptions the remote call raised that can be sent over the wire are raised.

        Internally this calls begin_call(method, *args).result(timeout=self.timeout)

        """
        return self.begin_call(method, *args, **kwargs).result(self.timeout)

    def notify(self, method, *args, **kwargs):
        """Perform a synchronous remote call where value no return value is desired.

        While faster than call it still blocks until the remote callback has been sent.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        """
        self.protocol.send_notification(method, args, kwargs)

    def begin_call(self, method, *args, **kwargs):
        """Perform an asynchronous remote call where the return value is not known yet.

        This returns immediately with a Deferred object. The Deferred object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        """
        d = Deferred(self.loop)
        d.request = self.request_num
        self.requests[self.request_num] = d
        self.protocol.send_request(d.request, method, args, kwargs)
        self.request_num += 1
        return d

    def response(self, msgid, response):
        """Handle a response message."""
        self.requests[msgid].callback(response)
        del self.requests[msgid]

    def error(self, msgid, error):
        """Handle a error message."""
        self.requests[msgid].errback(error)
        del self.requests[msgid]

class PickleProtocol(Protocol):
    def __init__(self, loop, factory, dispatch=Dispatch()):
        Protocol.__init__(self, loop)
        self.factory = factory
        self.dispatch = dispatch
        self._proxy = None
        self._proxy_deferreds = []
        self.handlers = {0:self.handle_request, 1:self.handle_notification,
            2:self.handle_response, 3:self.handle_error}
        self._buffer = bytes()
        self._data_handler = self.data_length

    def connection_made(self, address):
        """When a connection is made the proxy is available."""
        self._proxy = PickleProxy(self.loop, self)
        for d in self._proxy_deferreds:
            d.callback(self._proxy)

    def data(self, data):
        """Use a length prefixed protocol to give the length of a pickled
        message.

        """
        self._buffer = self._buffer + data

        while self._data_handler():
            pass

    def connection_lost(self, reason=None):
        """Tell the factory we lost our connection."""
        self.factory.lost_connection(self)
        self.factory = None

    def data_length(self):
        if len(self._buffer) >= 4:
            self._msglen = struct.unpack('!I', self._buffer[:4])[0]
            self._buffer = self._buffer[4:]
            self._data_handler = self.data_message
            return True
        return False

    def data_message(self):
        if len(self._buffer) >= self._msglen:
            msg = loads(self._buffer[:self._msglen])
            self.handlers[msg[0]](*msg)
            self._buffer = self._buffer[self._msglen:]
            self._data_handler = self.data_length
            return True
        return False

    def handle_request(self, msgtype, msgid, method, args, kwargs):
        """Handle a request."""
        response = None
        error = None
        exception = None

        try:
            response = self.dispatch.call(method, args, kwargs)
        except Exception as e:
            error = (e.__class__.__name__, str(e))
            exception = e

        if isinstance(response, Deferred):
            response.add_callback(self.send_response, msgid)
            response.add_errback(self.send_error, msgid)
        else:
            if exception is None:
                self.send_response(msgid, response)
            else:
                self.send_error(msgid, exception)

    def handle_notification(self, msgtype, method, args, kwargs):
        """Handle a notification."""
        self.dispatch.call(method, args, kwargs)

    def handle_response(self, msgtype, msgid, response):
        """Handle a response."""
        self._proxy.response(msgid, response)

    def handle_error(self, msgtype, msgid, error):
        """Handle an error."""
        self._proxy.error(msgid, error)

    def send(self, msg):
        length = struct.pack('!I', len(msg))
        self.transport.write(length)
        self.transport.write(msg)

    def send_request(self, msgid, method, args, kwargs):
        """Send a request."""
        msg = dumps([0, msgid, method, args, kwargs])
        self.send(msg)

    def send_notification(self, method, args, kwargs):
        """Send a notification."""
        msg = dumps([1, method, args, kwargs])
        self.send(msg)

    def send_response(self, msgid, response):
        """Send a response."""
        msg = dumps([2, msgid, response])
        self.send(msg)

    def send_error(self, msgid, error):
        """Send an error."""
        msg = dumps([3, msgid, error])
        self.send(msg)

    def proxy(self):
        """Return a Deferred that will result in a proxy object in the future."""
        d = Deferred(self.loop)
        self._proxy_deferreds.append(d)

        if self._proxy:
            d.callback(self._proxy)

        return d


class PickleProtocolFactory(ProtocolFactory):
    def __init__(self, dispatch=Dispatch()):
        ProtocolFactory.__init__(self)
        self.dispatch = dispatch
        self.protocol = PickleProtocol
        self.protocols = []

    def proxy(self, conn_number):
        """Return a proxy for a given connection number."""
        return self.protocols[conn_number].proxy()

    def build(self, loop):
        p = self.protocol(loop, self, self.dispatch)
        self.protocols.append(p)
        return p

    def lost_connection(self, p):
        """Called by the rpc protocol whenever it loses a connection."""
        self.protocols.remove(p)
