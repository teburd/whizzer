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

import sys
import signal
import logging
import pyev

sys.path.insert(0, '..')

from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.client import TcpClient

class EchoClientProtocol(Protocol):
    def __init__(self, loop):
        Protocol.__init__(self, loop)
        self.factory = factory

    def connection_made(self):
        """When the connection is made, send something."""
        self.transport.write(b'Echo Me')
        
    def data(self, data):
        #print("echo'd " + data)
        self.lose_connection()

def interrupt(watcher, events):
    watcher.loop.unloop()

if __name__ == "__main__":
    loop = pyev.default_loop()

    logger = logging.getLogger('echo_client')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    signal_watcher = pyev.Signal(signal.SIGINT, loop, interrupt)
    signal_watcher.start()

    factory = ProtocolFactory()
    factory.protocol = EchoClientProtocol

    client = TcpClient(loop, factory, logger, "127.0.0.1", 2000)
    client.connect()

    loop.loop()
