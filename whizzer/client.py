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

import socket
import signal
import logging

import pyev

from .transport import SocketTransport, ConnectionClosed
from .defer import Deferred

class Connection(object):
    """Represents a connection to a server from a client."""

    def __init__(self, loop, sock, protocol, client, logger):
        """Create a client connection."""
        self.loop = loop
        self.sock = sock
        self.protocol = protocol
        self.client = client
        self.logger = logger
        self.transport = SocketTransport(self.loop, self.sock,
                                         self.protocol.data, self.closed)
        self.protocol.make_connection(self.transport)
        self.transport.start()

    def closed(self, reason):
        """Callback performed when the transport is closed."""
        self.client.remove_connection(self)
        self.protocol.connection_lost(reason)
        if not isinstance(reason, ConnectionClosed):
            self.logger.warn("connection closed, reason %s" % str(reason))
        else:
            self.logger.info("connection closed")

    def close(self):
        """Close the connection."""
        self.transport.close()


class SocketClient(object):
    """A simple socket client."""
    def __init__(self, loop, factory, logger=logging):
        self.loop = loop
        self.factory = factory
        self.logger = logger
        self.connection = None
        self.connect_deferred = None
        self.sigint_watcher = pyev.Signal(signal.SIGINT, self.loop,
                                          self._interrupt)
        self.sigint_watcher.start()

    def _interrupt(self, watcher, events):
        if self.connection:
            self.connection.close()

    def _connect(self, sock, connect_arg):
        """Start watching the socket for it to be writtable."""
        
        self.logger.info("connecting to " + str(connect_arg))
        d = Deferred(self.loop)
        self.connect_deferred = d

        try:
            sock.connect(connect_arg)
            self.sock = sock
            self.connect_watcher = pyev.Io(self.sock, pyev.EV_WRITE, self.loop, self._connected)
            self.connect_watcher.start()
        except Exception as e:
            d.errback(e)

        return d

    def _connected(self, watcher, events):
        """When the socket is writtable, the socket is ready to be used."""
        self.connect_watcher.stop()
        self.connect_watcher = None
        protocol = self.factory.build(self.loop)
        self.connection = Connection(self.loop, self.sock, protocol, self,
                                     self.logger)
        
        self.logger.info("connected")
        self.connect_deferred.callback(protocol)

    def _disconnect(self):
        """Disconnect from a socket."""
        self.connection.close()
        self.connection = None

    def connect(self):
        """Should be overridden to create a socket and connect it.

        Once the socket is connected it should be passed to _connect.

        """

    def remove_connection(self, connection):
        self.connection = None


class UnixClient(SocketClient):
    """A unix client is a socket client that connects to a domain socket."""
    def __init__(self, loop, factory, path, logger=logging):
        SocketClient.__init__(self, loop, factory, logger)
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        return self._connect(sock, self.path)

    def disconnect(self):
        return self._disconnect()


class TcpClient(SocketClient):
    """A unix client is a socket client that connects to a domain socket."""
    def __init__(self, loop, factory, host, port, logger=logging):
        SocketClient.__init__(self, loop, factory, logger)
        self.host = host
        self.port = port

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return self._connect(sock, (self.host, self.port))

    def disconnect(self):
        return self._disconnect()
