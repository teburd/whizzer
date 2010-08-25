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
import socket
import interfaces

"""Base protocol objects. A new protocol implementation should implement these objects missing
methods or overload them as needed.
"""

class Protocol(interfaces.Protocol):
    """Basis of all client handling functionality."""
    def __init__(self, loop):
        self.loop = loop

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

class ProtocolFactory(interfaces.ProtocolFactory):
    """Constructor of protocols."""

    def __init__(self, loop):
        self.loop = loop
        self.protocol = None

    def build(self):
        """Build and return a Protocol object."""
        return self.protocol(self.loop)

