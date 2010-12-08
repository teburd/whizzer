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

from whizzer.protocol import Protocol, ProtocolFactory

class MockTransport(object):
    def __init__(self):
        self.closes = 0
        self.writes = 0

    def close(self):
        print("close")
        self.closes += 1

    def write(self):
        print("write")
        self.writes += 1

class MockLogger(object):
    def __init__(self):
        self.warns = []
        self.errors = []
        self.debugs = []
        self.infos = []

    def warn(self, message):
        print("warn: " + message)
        self.warns.append(message)

    def info(self, message):
        print("info: " + message)
        self.infos.append(message)

    def debug(self, message):
        print("debug: " + message)
        self.debugs.append(message)

    def error(self, message):
        print("error: " + message)
        self.errors.append(message)

class MockProtocol(Protocol):
    def __init__(self, loop):
        Protocol.__init__(self, loop)
        self.reads = 0
        self.errors = 0
        self.connections = 0
        self.losses = 0
        self.connected = False
        self.transport = None
        self._data = []
        self.reason = None

    def data(self, d):
        self.reads += 1
        self._data.append(d)
        print("reads " + str(self.reads))

    def connection_made(self, address):
        self.connections += 1
        print("connections " + str(self.connections))

    def connection_lost(self, reason=None):
        self.losses += 1
        self.reason = reason
        print("losses " + str(self.losses))

class MockFactory(ProtocolFactory):
    def __init__(self):
        ProtocolFactory.__init__(self)
        self.builds = 0

    def build(self, loop):
        self.builds += 1
        print("builds " + str(self.builds))
        return self.protocol(loop)


