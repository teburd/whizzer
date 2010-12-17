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

import pyev

import logbook

from whizzer.process import Process
from whizzer.server import UnixServer

from whizzer.rpc.dispatch import remote, ObjectDispatch
from whizzer.rpc.msgpackrpc import MsgPackProtocolFactory

logger = logbook.Logger(__name__)


class Service(Process):
    """A generic service class meant to be run in a process on its own and
    handle requests using RPC.

    """

    def __init__(self, loop, settings):
        """Create a service with a name."""
        Process.__init__(loop, self.run, (), {})
        self.loop = loop
        self.settings = settings
        self.logger = logbook.Logger(self.settings['name'])

    def listen(self):
        """Setup the service to listen for clients."""
        path = self.settings['name']
        dispatcher = ObjectDispatch(self)
        factory = MsgPackProtocolFactory(dispatcher)
        server = UnixServer(self.loop, factory, path)
        server.start()

    def run(self):
        """Run the event loop."""
        self.logger.info('{} starting'.format(self.settings['name']))
        self.loop.loop()

    @remote
    def stop(self, reason=None):
        """Shutdown the service with a reason."""
        self.logger.info('{} stopping'.format(self.settings['name']))
        self.loop.unloop(pyev.EVUNLOOP_ALL)
