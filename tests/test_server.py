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


import gc
import os
import sys
import socket
import unittest
import pyev

sys.path.insert(0, "..")

from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.server import UnixServer, TcpServer
from mocks import *
from common import loop

class TestServerCreation(unittest.TestCase):
    def test_tcp_server(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        server = TcpServer(loop, factory, "0.0.0.0", 2000)
        server = None

    def test_unix_server(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        server = UnixServer(loop, factory, "bogus")
        server = None
        # path should be cleaned up as soon as garbage collected
        gc.collect()
        self.assertTrue(not os.path.exists("bogus"))

class TestUnixServer(unittest.TestCase):
    def setUp(self):
        self.logger = MockLogger()
        self.factory = MockFactory()
        self.factory.protocl = MockProtocol
        self.path = "test"
        self.server = UnixServer(loop, self.factory, self.path, logger=self.logger)
        self.csock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def tearDown(self):
        self.logger = None
        self.factory = None
        self.server = None
        gc.collect()

    def cconnect(self):
        self.csock.connect(self.path)

    def test_start(self):
        self.server.start()

    def test_stop(self):
        self.server.start()
        self.server.stop()

if __name__ == '__main__':
    unittest.main()
