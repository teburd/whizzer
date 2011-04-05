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

import signal

import pyev

import logbook

from whizzer.process import Process
from whizzer.server import UnixServer
from whizzer.client import UnixClient

from whizzer.rpc.dispatch import remote, ObjectDispatch
from whizzer.rpc.msgpackrpc import MsgPackProtocolFactory

logger = logbook.Logger(__name__)


def spawn(cls, loop, name, path, *args, **kwargs):
    p = Process(loop, service, cls, loop, name, path, *args, **kwargs)
    p.start()
    return p

def service(cls, loop, name, path, *args, **kwargs):
    instance = cls(loop, name, path, *args, **kwargs)
    instance.run()


class ServiceProxy(object):
    """Proxy to a service."""

    def __init__(self, loop, path):
        self.loop = loop
        self.path = path
        self.proxy = None

    def connect(self):
        self.factory = MsgPackProtocolFactory()
        self.client = UnixClient(self.loop, self.factory, self.path)
        d = self.client.connect()
        d.add_callback(self.connected)
        return d

    def connected(self, result=None):
        d = self.factory.proxy(0)
        d.add_callback(self.set_proxy)

    def set_proxy(self, proxy):
        self.proxy = proxy

    def call(self, method, *args):
        return self.proxy.call(method, *args)

    def notify(self, method, *args):
        return self.proxy.notify(method, *args)

    def begin_call(self, method, *args):
        return self.proxy.begin_call(method, *args)


class Service(object):
    """A generic service class meant to be run in a process on its own and
    handle requests using RPC.

    """

    def __init__(self, loop, name, path):
        """Create a service with a name."""
        self.loop = loop
        self.name = name
        self.path = path
        self.logger = logbook.Logger(self.name)

    def signal_init(self):
        self.sigintwatcher = pyev.Signal(signal.SIGINT, self.loop, self._stop)
        self.sigintwatcher.start()
        self.sigtermwatcher = pyev.Signal(signal.SIGTERM, self.loop, self._terminate)
        self.sigtermwatcher.start()

    def _stop(self, watcher, events):
        self.stop(signal.SIGINT)

    def _terminate(self, watcher, events):
        self.terminate(signal.SIGTERM)

    def listen_init(self):
        """Setup the service to listen for clients."""
        self.dispatcher = ObjectDispatch(self)
        self.factory = MsgPackProtocolFactory(self.dispatcher)
        self.server = UnixServer(self.loop, self.factory, self.path)
        self.server.start()

    def run(self):
        """Run the event loop."""
        self.signal_init()
        self.listen_init()
        self.logger.info('starting')
        self.loop.start()

    @remote
    def stop(self, reason=None):
        """Shutdown the service with a reason."""
        self.logger.info('stopping')
        self.loop.stop(pyev.EVBREAK_ALL)

    @remote
    def terminate(self, reason=None):
        """Terminate the service with a reason."""
        self.logger.info('terminating')
        self.loop.unloop(pyev.EVUNLOOP_ALL)
