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


import os
import sys
import socket
import unittest
import pyev

sys.path.insert(0, "..")

from whizzer import server, errors, protocol

loop = pyev.default_loop()


class FakeProtocol(protocol.Protocol):
    def __init__(self):
        protocol.Protocol.__init__(self, loop)
        self.reads = 0
        self.errors = 0
        self.connections = 0
        self.losses = 0
        self.connected = False
        self.transport = None

    def make_connection(self, transport):
        """Called by the factory when the connection has been made.

        Most likely called right after the server call accept()

        """
        self.connected = True
        self.transport = transport
        self.connection_made()

    def lose_connection(self):
        """Closes the transport cleanly and informs the server that this connection has been closed."""
        self.transport.close()
        self.connected = False

    def data(self, d):
        self.reads += 1
        print("reads " + str(self.reads))

    def connection_made(self):
        self.connections += 1
        print("connections " + str(self.connections))

    def connection_lost(self, reason=None):
        self.losses += 1
        print("losses " + str(self.losses))

class FakeServer(object):
    def __init__(self):
        self.errors = 0
        self.losses = 0

    def connection_error(self, connection, error):
        self.errors += 1

    def connection_lost(self, connection):
        self.losses += 1


class TestSocketConnection(unittest.TestCase):
    def read(self, data):
        self.reads += 1

    def error(self, reason):
        self.errors += 1

    def setUp(self):
        # setup some blocking sockets to test the transport with
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind("test_sock")
        self.sock.listen(1)
        self.csock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.csock.connect("test_sock")
        self.ssock, self.saddr = self.sock.accept()
        self.reads = 0
        self.errors = 0

    def tearDown(self):
        self.sock = None
        self.csock = None
        self.ssock = None
        self.saddr = None
        os.remove("test_sock")
        self.reads = 0
        self.errors = 0

    def test_creation(self):
        t = server.SocketConnection(loop, self.ssock)

    def test_write(self):
        msg = b'hello'
        t = server.SocketConnection(loop, self.ssock)
        t.write(msg)
        loop.loop(pyev.EVLOOP_ONESHOT)
        rmsg = self.csock.recv(len(msg))
        self.assertEqual(rmsg, msg)

    def test_close(self):
        t = server.SocketConnection(loop, self.ssock)
        t.close()
        self.assertTrue(t.closed)

    def test_closed_write(self):
        t = server.SocketConnection(loop, self.ssock)
        t.close()
        self.assertRaises(errors.ConnectionClosedError, t.write, ("hello"))

    def test_overflow_write(self):
        t = server.SocketConnection(loop, self.ssock)
        self.assertRaises(errors.BufferOverflowError, t.write, ([x for x in range(0, 1024*1024)]))

    def test_read(self):
        t = server.SocketConnection(loop, self.ssock)
        t.read = self.read
        self.csock.send(b'hello')
        loop.loop(pyev.EVLOOP_ONESHOT)
        self.assertTrue(self.reads == 1)

    def test_error(self):
        t = server.SocketConnection(loop, self.ssock)
        t.error = self.error
        self.csock.close()
        t.write(b'hello')
        loop.loop(pyev.EVLOOP_ONESHOT)
        self.assertTrue(self.errors == 1)

class TestServerConnection(unittest.TestCase):
    def setUp(self):
        print("Doing Setup")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind("test_sock")
        self.sock.listen(1)
        self.csock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.csock.connect("test_sock")
        self.ssock, self.saddr = self.sock.accept()
        self.protocol = FakeProtocol()
        self.server = FakeServer()

    def tearDown(self):
        print("Doing Teardown")
        self.sock = None
        self.csock = None
        self.ssock = None
        self.saddr = None
        os.remove("test_sock")
        self.protocol = None
        self.server = None

    def test_creation(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        self.assertTrue(t.protocol.transport == t)
        self.assertTrue(t.protocol == self.protocol)
        self.assertTrue(t.server == self.server)

    def test_write(self):
        msg = b'hello'
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        t.write(msg)
        loop.loop(pyev.EVLOOP_ONESHOT)
        rmsg = self.csock.recv(len(msg))
        self.assertEqual(rmsg, msg)

    def test_close(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        t.close()
        self.assertTrue(t.closed)
        self.assertTrue(self.server.losses == 1)
        self.assertTrue(self.protocol.losses == 1)

    def test_closed_write(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        t.close()
        self.assertRaises(errors.ConnectionClosedError, t.write, ("hello"))

    def test_overflow_write(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        self.assertRaises(errors.BufferOverflowError, t.write, ([x for x in range(0, 1024*1024)]))

    def test_read(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        self.csock.send(b'hello')
        loop.loop(pyev.EVLOOP_ONESHOT)
        self.assertTrue(self.protocol.reads == 1)

    def test_error(self):
        t = server.ServerConnection(loop, self.ssock, self.protocol, self.server)
        self.protocol.make_connection(t)
        self.csock.close()
        t.write(b'hello')
        loop.loop(pyev.EVLOOP_ONESHOT)
        self.assertTrue(self.protocol.losses == 1)
        self.assertTrue(self.server.errors == 1)


if __name__ == '__main__':
    unittest.main()
