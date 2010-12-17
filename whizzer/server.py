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
import signal
import socket
import logbook
import pyev

from whizzer.transport import SocketTransport, ConnectionClosed

logger = logbook.Logger(__name__)


class Connection(object):
    """A connection to the server from a remote client."""
    def __init__(self, loop, sock, address, protocol, server):
        """Create a server connection."""
        self.loop = loop
        self.sock = sock
        self.address = address
        self.protocol = protocol
        self.server = server
        self.transport = SocketTransport(self.loop, self.sock, self.protocol.data, self.closed)

    def make_connection(self):
        self.transport.start()
        self.protocol.make_connection(self.transport, self.address)

    def closed(self, reason):
        """Callback performed when the transport is closed."""
        self.server.remove_connection(self)
        self.protocol.connection_lost(reason)
        if not isinstance(reason, ConnectionClosed):
            logger.warn("connection closed, reason: %s" % str(reason))
        else:
            logger.info("connection closed")

    def close(self):
        """Close the connection."""
        self.transport.close()


class ShutdownError(Exception):
    """Error signifying the server has already been shutdown and cannot be
    used further."""

class SocketServer(object):
    """A socket server."""
    def __init__(self, loop, factory, sock, address):
        """Socket server listens on a given socket for incoming connections.
        When a new connection is available it accepts it and creates a new
        Connection and Protocol to handle reading and writting data.

        loop -- pyev loop
        factory -- protocol factory (object with build(loop) method that returns a protocol object)
        sock -- socket to listen on

        """
        self.loop = loop
        self.factory = factory
        self.sock = sock
        self.address = address
        self.connections = set()
        self._closing = False
        self._shutdown = False
        self.interrupt_watcher = pyev.Signal(signal.SIGINT, self.loop, self._interrupt)
        self.interrupt_watcher.start()
        self.read_watcher = pyev.Io(self.sock, pyev.EV_READ, self.loop, self._readable)

    def start(self):
        """Start the socket server.
       
        The socket server will begin accepting incoming connections.
        
        """
        if self._shutdown:
            raise ShutdownError()

        self.read_watcher.start()
        logger.info("server started listening on {}".format(self.address))

    def stop(self):
        """Stop the socket server.
        
        The socket server will stop accepting incoming connections.

        The connections already made will continue to exist.

        """
        if self._shutdown:
            raise ShutdownError()

        self.read_watcher.stop()
        logger.info("server stopped listening on {}".format(self.address))

    def shutdown(self, reason = ConnectionClosed()):
        """Shutdown the socket server.

        The socket server will stop accepting incoming connections.

        All connections will be dropped.

        """
        if self._shutdown:
            raise ShutdownError()
        
        self.stop()
       
        self._closing = True
        for connection in self.connections:
            connection.close()
        self.connections = set()
        self._shutdown = True
        if isinstance(reason, ConnectionClosed):
            logger.info("server shutdown")
        else:
            logger.warn("server shutdown, reason %s" % str(reason))

    def _interrupt(self, watcher, events):
        """Handle the interrupt signal sanely."""
        self.shutdown()

    def _readable(self, watcher, events):
        """Called by the pyev watcher (self.read_watcher) whenever the socket
        is readable.
   
        This means either the socket has been closed or there is a new
        client connection waiting.

        """
        protocol = self.factory.build(self.loop)
        try:
            sock, address = self.sock.accept()
            connection = Connection(self.loop, sock, address, protocol, self)
            self.connections.add(connection)
            connection.make_connection()
            logger.debug("added connection")
        except IOError as e:
            self.shutdown(e)

    def remove_connection(self, connection):
        """Called by the connections themselves when they have been closed."""
        if not self._closing:
            self.connections.remove(connection)
            logger.debug("removed connection")

class _PathRemoval(object):
    """Remove a path when the object dies.
        
    Used by UnixServer so that a __del__ method is not needed for UnixServer.

    """
    def __init__(self, path):
        self.path = path

    def __del__(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

class UnixServer(SocketServer):
    """A unix server is a socket server that listens on a domain socket."""
    def __init__(self, loop, factory, path, backlog=256):
        self.address = path
        self.path_removal = _PathRemoval(self.address)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        self.sock.listen(backlog)
        self.sock.setblocking(False)
        SocketServer.__init__(self, loop, factory, self.sock, self.address)

    def shutdown(self):
        """Shutdown the socket unix socket server ensuring the unix socket is
        removed.
        
        """
        err = None
        SocketServer.shutdown(self)

class TcpServer(SocketServer):
    """A tcp server is a socket server that listens on a internet socket."""
    def __init__(self, loop, factory, host, port, backlog=256):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(backlog)
        self.sock.setblocking(False)
        SocketServer.__init__(self, loop, factory, self.sock, self.address)
