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

"""Ping Pong Web, Nicholas Piel's Asynchronous Web Server Test.

This ping pong web server compares extremely well to everything else
listed on Nicholas's website.

http://nichol.as/asynchronous-servers-in-python

"""

import sys

import pyev

sys.path.insert(0, '..')

import whizzer

class PongProtocol(whizzer.Protocol):
    def connection_made(self):
        self.transport.write("HTTP/1.0 200 OK\r\nContent-Length: 5 \r\n\r\nPong!\r\n")
        self.lose_connection()

loop = pyev.default_loop()
sigwatcher = whizzer.signal_handler(loop)
factory = whizzer.ProtocolFactory()
factory.protocol = PongProtocol
server = whizzer.TcpServer(loop, factory, "0.0.0.0", 8000, 500)

sigwatcher.start()
server.start()
loop.loop()
