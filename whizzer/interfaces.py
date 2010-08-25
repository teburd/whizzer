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

class Connection(object):
    """Defines the basis for a connection template object."""

    def read(self, data):
        """Called whenever the connection has read some data.
       
        data -- bytes object
        
        """

    def write(self, data):
        """Called to initiate a write to the connection.

        data -- bytes object

        """

    def error(self, error):
        """Called to initiate error handling whenever the connection has
        caught an error.

        """

    def close(self):
        """Called to close the connection from the owner of the connection."""

class Protocol(object):
    """Basis of all client handling functionality."""
    
    def make_connection(self, transport):
        """Called by the factory when the connection has been made.

        Most likely called right after the server call accept()

        """

    def lose_connection(self):
        """Closes the transport cleanly and informs the server that this connection has been closed."""

    def connection_lost(self, reason=None):
        """Handle a lost connection."""

    def connection_made(self):
        """Handle a new connection."""

    def data(self, data):
        """Handle incoming data.

        data -- bytes containing new data from the transport.

        """

class ProtocolFactory(object):
    """Constructor of protocols."""
    def build(self):
        """Build and return a Protocol object."""
