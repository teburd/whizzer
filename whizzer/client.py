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
import logbook
import pyev

from .transport import SocketTransport, ConnectionClosed
from .defer import Deferred

logger = logbook.Logger('client')


class TimeoutError(Exception):
    pass


class Connection(object):
    """Represents a connection to a server from a client."""

    def __init__(self, loop, sock, addr, protocol, client):
        """Create a client connection."""
        self.loop = loop
        self.sock = sock
        self.addr = addr
        self.protocol = protocol
        self.client = client
        logger.info('making transport')
        self.transport = SocketTransport(self.loop, self.sock,
                                         self.protocol.data, self.closed)
        logger.info('protocol.make_connection')
        self.protocol.make_connection(self.transport, self.addr)
        logger.info('transport.start()')
        self.transport.start()
        logger.info('transport started')

    def closed(self, reason):
        """Callback performed when the transport is closed."""
        self.client.remove_connection(self)
        self.protocol.connection_lost(reason)
        if not isinstance(reason, ConnectionClosed):
            logger.warn("connection closed, reason {}".format(reason))
        else:
            logger.info("connection closed")

    def close(self):
        """Close the connection."""
        self.transport.close()


class SocketClient(object):
    """A simple socket client."""
    def __init__(self, loop, factory):
        self.loop = loop
        self.factory = factory
        self.connection = None
        self.connect_deferred = None
        self.sigint_watcher = pyev.Signal(signal.SIGINT, self.loop,
                                          self._interrupt)
        self.sigint_watcher.start()

    def _interrupt(self, watcher, events):
        if self.connection:
            self.connection.close()

    def _connect(self, sock, addr, timeout):
        """Start watching the socket for it to be writtable."""
        
        logger.debug("connecting to {}".format(addr))
        self.sock = sock
        self.addr = addr
        d = Deferred(self.loop)
        self.connect_deferred = d

        try:
            logger.info('calling connect')
            self.connect_watcher = pyev.Io(self.sock, pyev.EV_WRITE, self.loop, self._connected)
            self.connect_watcher.start()
            self.sock.connect(addr)
            logger.info('connect called')
            self.timeout_watcher = pyev.Timer(timeout, 0.0, self.loop, self._connect_timeout)
            self.timeout_watcher.start()
            logger.info('waiting for writtable socket')
        except Exception as e:
            d.errback(e)

        return d

    def _connected(self, watcher, events):
        """When the socket is writtable, the socket is ready to be used."""
        logger.debug('socket connected, building protocol')
        self.connect_watcher.stop()
        self.timeout_watcher.stop()
        self.connect_watcher = None
        self.timeout_watcher = None
        self.protocol = self.factory.build(self.loop)
        self.connection = Connection(self.loop, self.sock, self.addr,
            self.protocol, self) 
        
        logger.info("connected to {}".format(self.addr))
        self.timeout_watcher = pyev.Timer(0.1, 0.0, self.loop, lambda watcher, events: self.connect_deferred.callback(self.protocol))
        self.timeout_watcher.start()

    def _connect_timeout(self, watcher, events):
        """Connect timed out."""
        self.connect_watcher.stop()
        self.timeout_watcher.stop()
        self.connect_watcher = None
        self.timeout_watcher = None
        self.connect_deferred.errback(TimeoutError())


    def _disconnect(self):
        """Disconnect from a socket."""
        self.connection.close()
        self.connection = None

    def connect(self, timeout=5):
        """Should be overridden to create a socket and connect it.

        Once the socket is connected it should be passed to _connect.

        """

    def remove_connection(self, connection):
        self.connection = None


class UnixClient(SocketClient):
    """A unix client is a socket client that connects to a domain socket."""
    def __init__(self, loop, factory, path):
        SocketClient.__init__(self, loop, factory)
        self.path = path

    def connect(self, timeout=5.0):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        return self._connect(sock, self.path, timeout)

    def disconnect(self):
        return self._disconnect()


class TcpClient(SocketClient):
    """A unix client is a socket client that connects to a domain socket."""
    def __init__(self, loop, factory, host, port):
        SocketClient.__init__(self, loop, factory)
        self.host = host
        self.port = port

    def connect(self, timeout=5.0):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return self._connect(sock, (self.host, self.port), timeout)

    def disconnect(self):
        return self._disconnect()
