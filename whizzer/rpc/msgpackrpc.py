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


import msgpack

from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.defer import Deferred

from whizzer.rpc.proxy import Proxy
from whizzer.rpc.dispatch import Dispatch


class MsgPackProxy(Proxy):
    """A MessagePack-RPC Proxy."""

    def __init__(self, loop, protocol):
        """MsgPackProxy

        loop -- A pyev loop.
        protocol -- An instance of MsgPackProtocol.

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

    def call(self, method, *args):
        """Perform a synchronous remote call where the returned value is given immediately.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        Any exceptions the remote call raised that can be sent over the wire are raised.

        Internally this calls begin_call(method, *args).result(timeout=self.timeout)

        """
        return self.begin_call(method, *args).result(self.timeout)

    def notify(self, method, *args):
        """Perform a synchronous remote call where value no return value is desired.

        While faster than call it still blocks until the remote callback has been sent.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        """
        self.protocol.send_notification(method, args)

    def begin_call(self, method, *args):
        """Perform an asynchronous remote call where the return value is not known yet.

        This returns immediately with a Deferred object. The Deferred object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        """
        d = Deferred(self.loop)
        d.request = self.request_num
        self.requests[self.request_num] = d
        self.protocol.send_request(d.request, method, args)
        self.request_num += 1
        return d

    def response(self, msgid, error, result):
        """Handle a results message given to the proxy by the protocol object."""
        if error:
            self.requests[msgid].errback(Exception(str(error)))
        else:
            self.requests[msgid].callback(result)
        del self.requests[msgid]

class MsgPackProtocol(Protocol):
    def __init__(self, loop, factory, dispatch=Dispatch()):
        Protocol.__init__(self, loop)
        self.factory = factory
        self.dispatch = dispatch
        self._proxy = None
        self._proxy_deferreds = []
        self.handlers = {0:self.request, 1:self.response, 2:self.notify}
        self.unpacker = msgpack.Unpacker()

    def connection_made(self, address):
        """When a connection is made the proxy is available."""
        self._proxy = MsgPackProxy(self.loop, self)
        for d in self._proxy_deferreds:
            d.callback(self._proxy)

    def response(self, msgtype, msgid, error, result):
        """Handle an incoming response."""
        self._proxy.response(msgid, error, result)

    def notify(self, msgtype, method, params):
        """Handle an incoming notify request."""
        self.dispatch.call(method, params)

    def request(self, msgtype, msgid, method, params=[]):
        """Handle an incoming call request."""
        result = None
        error = None
        exception = None

        try:
            result = self.dispatch.call(method, params)
        except Exception as e:
            error = (e.__class__.__name__, str(e))
            exception = e

        if isinstance(result, Deferred):
            result.add_callback(self._result, msgid)
            result.add_errback(self._error, msgid)
        else:
            self.send_response(msgid, error, result)

    def data(self, data):
        """Use msgpack's streaming feed feature to build up a set of lists.
        
        The lists should then contain the messagepack-rpc specified items.

        This should be outrageously fast.

        """
        self.unpacker.feed(data)
        for msg in self.unpacker:
            self.handlers[msg[0]](*msg)

    def _result(self, result, msgid):
        self.send_response(msgid, None, result)

    def _error(self, exception, msgid):
        self.send_response(msgid, exception, None)

    def send_request(self, msgid, method, params):
        msg = msgpack.packb([0, msgid, method, params])
        self.transport.write(msg)
  
    def send_response(self, msgid, error, result):
        msg = msgpack.packb([1, msgid, error, result])
        self.transport.write(msg)

    def send_notification(self, method, params):
        msg = msgpack.packb([2, method, params])
        self.transport.write(msg)

    def proxy(self):
        """Return a Deferred that will result in a proxy object in the future."""
        d = Deferred(self.loop)
        self._proxy_deferreds.append(d)

        if self._proxy:
            d.callback(self._proxy)

        return d

    def connection_lost(self, reason=None):
        """Tell the factory we lost our connection."""
        self.factory.lost_connection(self)
        self.factory = None


class MsgPackProtocolFactory(ProtocolFactory):
    def __init__(self, dispatch=Dispatch()):
        ProtocolFactory.__init__(self)
        self.dispatch = dispatch
        self.protocol = MsgPackProtocol
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
