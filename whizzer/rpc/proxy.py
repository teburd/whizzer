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

import logbook 

from whizzer.defer import Deferred

logger = logbook.Logger(__name__)


class Proxy(object):
    """Proxy object that performs remote calls."""

    def __init__(self, loop, protocol):
        """MsgPackProxy

        loop -- A pyev loop.
        protocol -- An instance of RPCProtocol.

        """
        self.loop = loop
        self.protocol = protocol
        self.request_num = 0
        self.requests = dict()
        
        #: synchronous call() timeout
        self.timeout = None

    def call(self, method, *args):
        """Perform a synchronous remote call where the returned value is given immediately.

        This may block for sometime in certain situations. If it takes more than the Proxies
        set timeout then a TimeoutError is raised.

        Any exceptions the remote call raised that can be sent over the wire are raised.

        Internally this calls begin_call(method, *args).result(timeout=self.timeout)

        """
        return self.begin_call(method, *args).result(self.timeout)

    def notify(self, method, *args):
        """Perform a synchronous remote call where no return value is desired."""

        self.protocol.send_notification(method, args)

    def begin_call(self, method, *args):
        """Perform an asynchronous remote call where the return value is not known yet.

        This returns immediately with a Deferred object. The Deferred object may then be
        used to attach a callback, force waiting for the call, or check for exceptions.

        """
        d = Deferred(self.loop, logger=logger)
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


