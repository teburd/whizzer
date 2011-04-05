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

from whizzer.transport import SocketTransport, ConnectionClosed, BufferOverflowError
from common import loop

fpath = os.path.dirname(__file__)

class TestSocketTransport(unittest.TestCase):
    def setUp(self):
        # setup some blocking sockets to test the transport with
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(fpath + "/test_sock")
        self.sock.listen(1)
        self.csock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.csock.connect(fpath + "/test_sock")
        self.ssock, self.saddr = self.sock.accept()
        self.data = [] 
        self.reason = None

    def tearDown(self):
        self.sock = None
        self.csock = None
        self.ssock = None
        self.saddr = None
        os.remove(fpath + "/test_sock")
        self.data = []
        self.reason = None

    def read(self, data):
        print("got " + str(data))
        self.data = data

    def close(self, reason):
        self.reason = reason

    def test_creation(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)

    def test_write(self):
        msg = b'hello'
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.write(msg)
        loop.start(pyev.EVRUN_NOWAIT)
        rmsg = self.csock.recv(len(msg))
        self.assertEqual(rmsg, msg)

    def test_close(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.close()
        self.assertTrue(t.closed)
        self.assertTrue(isinstance(self.reason, ConnectionClosed))

    def test_closed_write(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.close()
        self.assertRaises(ConnectionClosed, t.write, ("hello"))

    def test_closed_start(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.close()
        self.assertRaises(ConnectionClosed, t.start)

    def test_closed_stop(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.close()
        self.assertRaises(ConnectionClosed, t.stop)

    def test_stop(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.stop()

    def test_stop(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.stop()

    def test_stop_buffered_write(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        count = 0
        msg = b'hello'
        while(t.write != t.buffered_write):
            count += 1
            t.write(msg)
        t.write(msg)
        t.stop()
        self.csock.recv(count*len(msg))
        t.start()
        loop.start(pyev.EVRUN_NOWAIT)
        self.assertTrue(t.write == t.unbuffered_write)

    def test_close_buffered_write(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        count = 0
        msg = b'hello'
        while(t.write != t.buffered_write):
            count += 1
            t.write(msg)
        t.write(msg)
        t.close()
        self.assertRaises(ConnectionClosed, t.write, msg)

    def test_buffered_write(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        count = 0
        msg = b'hello'
        while(t.write != t.buffered_write):
            count += 1
            t.write(msg)
        t.write(msg)
        self.csock.recv(count*len(msg))
        loop.start(pyev.EVRUN_NOWAIT)
        self.assertTrue(t.write == t.unbuffered_write)

    def test_overflow_write(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        self.assertRaises(BufferOverflowError, t.write, bytes([1 for x in range(0, 1024*1024)]))

    def test_read(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        t.start()
        self.csock.send(b'hello')
        loop.start(pyev.EVRUN_NOWAIT)
        self.assertEqual(self.data, b'hello')

    def test_error(self):
        t = SocketTransport(loop, self.ssock, self.read, self.close)
        self.csock.close()
        t.write(b'hello')
        loop.start(pyev.EVRUN_NOWAIT)
        self.assertTrue(self.reason is not None)

if __name__ == '__main__':
    unittest.main()
