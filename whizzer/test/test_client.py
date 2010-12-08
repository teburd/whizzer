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

import os
import sys
import time
import unittest
import socket

import pyev

from whizzer.defer import Deferred
from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.client import TcpClient, UnixClient
from mocks import *
from common import loop

class TestClientCreation(unittest.TestCase):
    def test_tcp_client(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        client = TcpClient(loop, MockFactory(), "0.0.0.0", 2000)
    
    def test_unix_client(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        client = UnixClient(loop, MockFactory(), "bogus")
        
class TestUnixClient(unittest.TestCase):
    """Functional test for UnixClient."""
    def setUp(self):
        self.path = "test"
        self.ssock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.ssock.bind(self.path)
        self.ssock.listen(5)
      
        self.factory = MockFactory()
        self.factory.protocol = MockProtocol
        self.client = UnixClient(loop, self.factory, self.path)

        self._connected = False

    def tearDown(self):
        self.ssock.close()
        os.remove(self.path)
        self.client = None
        self.factory = None
        self.ssock = None
    
        self._connected = False
    
    def connected(self, protocol):
        self.assertTrue(isinstance(protocol, MockProtocol))
        self.protocol = protocol
        self._connected = True

    def test_connect(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()

    def test_lose_connection(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.protocol.lose_connection()
     
    def test_interrupt(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.client._interrupt(None, None)
        self.assertTrue(self.client.connection is None)

    def test_disconnect(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.client.disconnect()
        self.assertTrue(self.client.connection is None)

class TestTcpClient(unittest.TestCase):
    """Functional test for TcpClient."""
    def setUp(self):
        self.port = 6000
        self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
            try:
                self.ssock.bind(("0.0.0.0", self.port))
                break
            except IOError as e:
                self.port += 1
        
        self.ssock.listen(5)
      
        self.factory = MockFactory()
        self.factory.protocol = MockProtocol
        self.client = TcpClient(loop, self.factory, "0.0.0.0", self.port)
        self._connected = False

    def tearDown(self):
        self.ssock.close()
        self.client = None
        self.factory = None
        self.ssock = None
        self._connected = False
    
    def connected(self, protocol):
        self.assertTrue(isinstance(protocol, MockProtocol))
        self.protocol = protocol
        self._connected = True

    def test_connect(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()

    def test_lose_connection(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.protocol.lose_connection()
     
    def test_interrupt(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.client._interrupt(None, None)
        self.assertTrue(self.client.connection is None)

    def test_disconnect(self):
        d = self.client.connect()
        self.assertTrue(isinstance(d, Deferred))
        d.add_callback(self.connected)
        (csock, addr) = self.ssock.accept()
        d.result()
        self.client.disconnect()
        self.assertTrue(self.client.connection is None)

if __name__ == '__main__':
    unittest.main()
