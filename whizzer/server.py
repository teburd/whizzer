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
import socket

import pyev

from .interfaces import Connection
from .errors import ConnectionClosedError, BufferOverflowError

class SocketConnection(Connection):
    """A buffered writtable transport."""
    def __init__(self, loop, sock, max_size = 1024*512):
        self.loop = loop
        self.sock = sock
        self.sock.setblocking(False)
        self.read_watcher = pyev.Io(self.sock, pyev.EV_READ, self.loop, self._do_read)
        self.read_watcher.start()
        self.write_watcher = pyev.Io(self.sock, pyev.EV_WRITE, self.loop, self._do_write)
        self.write_buffer = bytearray()
        self.max_size = max_size # 512KB is quite substantial for a send/recv buffer
        self.read_fn = None
        self.error_fn = None
        self.closed = False
        self.err = None
        self.writtable = True

    def write(self, buf):
        """Appends a bytes like object to the transport write buffer.

        This actually only buffers if necessary. It avoids it if it can because it slows things down quite a bit.

        Raises BufferOverflowError if bytes like object would cause the buffer to grow beyond the
        specified maximum.

        """
        if self.closed:
            raise ConnectionClosedError()

        result = 0
        if self.writtable:
            try:
                result = self._write(buf)
            except IOError as e:
                self._do_error(e)
                return
            except OSError as e:
                self._do_error(e)
                return

        if result != len(buf):
            self.writtable = False
            if len(buf) + len(self.write_buffer) > self.max_size:
                raise BufferOverflowError()
            else:
                self.write_buffer.extend(buf)

            if not self.write_watcher.active:
                self.write_watcher.start()
        
    def _do_write(self, watcher, events):
        if self.closed:
            return
        if len(self.write_buffer) == 0:
            self.write_watcher.stop()
            self.writtable = True

        try:
            sent = self._write(self.write_buffer)
            self.write_buffer = self.write_buffer[written:]
        except socket.error as e:
            self._do_error(e)

    def _write(self, buf):
        return self.sock.send(bytes(buf))

    def _do_read(self, watcher, events):
        if self.closed:
            return
        try:
            data = self.sock.recv(4096)
            if len(data) == 0:
                self._do_error(IOError('Connection Closed'))
            else:
                self.read(data)

        except IOError as e:
            self._do_error(e)

    def _do_error(self, e):
        self.error(e)
        self._do_close()

    def close(self):
        self._do_close()

    def _do_close(self):
        if not self.closed:
            self.closed = True
            self.write_watcher.stop()
            self.read_watcher.stop()
            self.sock.close()
            self.sock = None

class ServerConnection(SocketConnection):
    """Represents a connection to the server. A SocketConnection template
    implementation.
    """
    def __init__(self, loop, sock, protocol, server):
        SocketConnection.__init__(self, loop, sock)
        self.server = server
        self.protocol = protocol

    def read(self, data):
        """Pass along the data from the real connection to the protocol."""
        self.protocol.data(data)

    def error(self, error):
        """There as an error, so clear any circular references and
        tell the protocol.
        """

        self.protocol.connection_lost(error)
        self.protocol.transport = None
        self.server.connection_error(self, error)
        
    def close(self):
        """Close a client connection and clear circular references.
        
        This should not be called by a protocol. This should be called
        by the server holding on to this connection.
        
        """
        SocketConnection.close(self)

        self.protocol.connection_lost()
        self.protocol.transport = None
        self.server.connection_lost(self)


class SocketServer(SocketConnection):
    """A socket server."""

    def __init__(self, loop, factory, sock):
        SocketConnection.__init__(self, loop, sock)
        self.factory = factory
        self.connections = set()
        self.closing = False

    def _do_read(self, watcher, events):
        """Overload the do_read method because recv 
        is not a valid method on a listening socket.
        """
        self.read([])
    
    def read(self, data):
        """When a socket being listened on is readable it simply means
        a new connection is waiting to be accepted, so accept it.

        This means creating a protocol using the given factory and a 
        connection object that holds on to and uses the protocol.

        """
        protocol = self.factory.build()
        try:
            sock, addr = self.sock.accept()
            connection = ServerConnection(self.loop, sock, protocol, self)
            protocol.make_connection(connection)
            self.connections.add(connection)
        except IOError as e:
            protocol = None
            self._do_error(e)
            
    def error(self, error):
        """The socket we're listening to had an error, so kill all the clients and clean up."""
        self.closing = True
        for connection in self.connections:
            connection.close()
        self.connections = set()

    def close(self):
        self.closing = True
        SocketConnection.close(self)
        for connection in self.connections:
            connection.close()
        self.connections = set()

    def connection_error(self, connection, error):
        """Handle an error on one of the client connections gracefully."""
        connection.server = None
        self.connections.remove(connection)

    def connection_lost(self, connection):
        """Handle a connection lost on one of the client connections gracefully."""
        connection.server = None
        if not self.closing:
            self.connections.remove(connection)

class UnixServer(SocketServer):
    """A unix server is a socket server that listens on a domain socket."""
    def __init__(self, loop, factory, path, conn_limit=5):
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        self.sock.listen(conn_limit)
        SocketServer.__init__(self, loop, factory, self.sock)

    def close(self):
        err = None
        try:
            SocketServer.close(self)
        except Exception as e:
            err = e
        finally:
            os.remove(self.path)
            if err:
                raise err

class TcpServer(SocketServer):
    """A tcp server is a socket server that listens on a internet socket."""
    def __init__(self, loop, factory, host, port, conn_limit=5):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(conn_limit)
        SocketServer.__init__(self, loop, factory, self.sock)
