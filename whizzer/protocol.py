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

class Protocol(object):
    """Basis of all client handling functionality."""
    def __init__(self, loop):
        self.loop = loop

    def make_connection(self, transport, address):
        """Called externally when the transport is ready."""
        self.connected = True
        self.transport = transport
        self.connection_made(address)

    def connection_made(self, address):
        """Called when the connection is ready to use."""

    def connection_lost(self, reason):
        """Called when the connection has been lost."""

    def data(self, data):
        """Handle an incoming stream of data."""

    def lose_connection(self):
        self.transport.close()

class ProtocolFactory(object):
    """Protocol factory."""
    def build(self, loop):
        """Build and return a Protocol object."""
        return self.protocol(loop)

