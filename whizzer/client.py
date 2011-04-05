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

from whizzer.transport import SocketTransport, ConnectionClosed
from whizzer.defer import Deferred

logger = logbook.Logger(__name__)


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
        logger.debug('making transport')
        self.transport = SocketTransport(self.loop, self.sock,
                                         self.protocol.data, self.closed)
        logger.debug('protocol.make_connection')
        self.protocol.make_connection(self.transport, self.addr)
        logger.debug('transport.start()')
        self.transport.start()
        logger.debug('transport started')

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


class ConnectorStartedError(Exception):
    """Connectors may only be started once."""


class Connector(object):
    """State machine for a connection to a remote socket."""

    def __init__(self, loop, sock, addr, timeout):
        self.loop = loop
        self.sock = sock
        self.addr = addr
        self.timeout = timeout
        self.connect_watcher = pyev.Io(self.sock, pyev.EV_WRITE, self.loop, self._connected)
        self.timeout_watcher = pyev.Timer(self.timeout, 0.0, self.loop, self._timeout)
        self.deferred = Deferred(self.loop)
        self.started = False
        self.connected = False
        self.timedout = False
        self.errored = False

    def start(self):
        """Start the connector state machine."""
        if self.started:
            raise ConnectorStartedError()

        self.started = True

        try:
            self.connect_watcher.start()
            self.timeout_watcher.start()
            self.sock.connect(self.addr)
        except IOError as e:
            self.errored = True
            self._finish()
            self.deferred.errback(e)

        return self.deferred

    def cancel(self):
        """Cancel a connector from completing."""
        if self.started and not self.connected and not self.timedout:
            self.connect_watcher.stop()
            self.timeout_watcher.stop()

    def _connected(self, watcher, events):
        """Connector is successful, return the socket."""
        self.connected = True
        self._finish()
        self.deferred.callback(self.sock)

    def _timeout(self, watcher, events):
        """Connector timed out, raise a timeout error."""
        self.timedout = True
        self._finish()
        self.deferred.errback(TimeoutError())

    def _finish(self):
        """Finalize the connector."""
        self.connect_watcher.stop()
        self.timeout_watcher.stop()


class SocketClientConnectedError(object):
    """Raised when a client is already connected."""


class SocketClientConnectingError(object):
    """Raised when a client is already connecting."""


class SocketClient(object):
    """A simple socket client."""
    def __init__(self, loop, factory):
        self.loop = loop
        self.factory = factory
        self.connector = None
        self.connection = None
        self.connect_deferred = None
        
        self.sigint_watcher = pyev.Signal(signal.SIGINT, self.loop,
                                          self._interrupt)
        self.sigint_watcher.start()

        self.connector = None
        self.sock = None
        self.addr = None

    def _interrupt(self, watcher, events):
        if self.connection:
            self.connection.close()

    def _connect(self, sock, addr, timeout):
        """Start watching the socket for it to be writtable."""
        if self.connection:
            raise SocketClientConnectedError()

        if self.connector:
            raise SocketClientConnectingError()

        self.connect_deferred = Deferred(self.loop)
        self.sock = sock
        self.addr = addr
        self.connector = Connector(self.loop, sock, addr, timeout)
        self.connector.deferred.add_callback(self._connected)
        self.connector.deferred.add_errback(self._connect_failed)
        self.connector.start()

        return self.connect_deferred

    def _connected(self, sock):
        """When the socket is writtable, the socket is ready to be used."""
        logger.debug('socket connected, building protocol')
        self.protocol = self.factory.build(self.loop)
        self.connection = Connection(self.loop, self.sock, self.addr,
            self.protocol, self) 
        self.connector = None
        self.connect_deferred.callback(self.protocol)

    def _connect_failed(self, reason):
        """Connect failed."""
        self.connector = None
        self.connect_deferred.errback(reason)

    def _disconnect(self):
        """Disconnect from a socket."""
        if self.connection:
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
