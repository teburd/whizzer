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
import errno
import pyev


class ConnectionClosed(Exception):
    """Signifies the connection is no longer valid."""


class BufferOverflowError(Exception):
    """Signifies something would cause a buffer overflow."""


class SocketTransport(object):
    """A buffered writtable transport."""

    def __init__(self, loop, sock, read_cb, close_cb, max_size=1024 * 512):
        """Creates a socket transport that will perform the given functions
        whenever the socket is readable or has an error. Writting to the
        transport by default simply calls the send() function and checks for
        errors. If the error happens to be that the socket is unavailable
        (its buffer is full) the write is buffered until the max_size limit is
        reached writting out of the buffer whenever the socket is writtable.

        loop -- pyev loop
        sock -- python socket object
        read_cb -- read function (callback when the socket is read)
        close_cb -- closed function (callback when the socket has been closed)
        max_size -- maximum user space buffer

        """
        self.loop = loop
        self.sock = sock
        self.read_cb = read_cb
        self.close_cb = close_cb
        self.max_size = max_size
        self.sock.setblocking(False)
        self.read_watcher = pyev.Io(self.sock, pyev.EV_READ, self.loop,
                                   self._readable)
        self.write_watcher = pyev.Io(self.sock, pyev.EV_WRITE, self.loop,
                                     self._writtable)
        self.write_buffer = bytearray()
        self.closed = False

        self.write = self.unbuffered_write

    def start(self):
        """Start watching the socket."""
        if self.closed:
            raise ConnectionClosed()

        self.read_watcher.start()
        if self.write == self.buffered_write:
            self.write_watcher.start()

    def stop(self):
        """Stop watching the socket."""
        if self.closed:
            raise ConnectionClosed()

        if self.read_watcher.active:
            self.read_watcher.stop()
        if self.write_watcher.active:
            self.write_watcher.stop()

    def write(self, buf):
        """Write data to a non-blocking socket.

        This function is aliased depending on the state of the socket.

        It may either be unbuffered_write or buffered_write, the caller
        should not care.

        buf -- bytes to send

        """

    def unbuffered_write(self, buf):
        """Performs an unbuffered write, the default unless socket.send does
        not send everything, in which case an unbuffered write is done and the
        write method is set to be a buffered write until the buffer is empty
        once again.

        buf -- bytes to send

        """
        if self.closed:
            raise ConnectionClosed()

        result = 0
        try:
            result = self.sock.send(buf)
        except EnvironmentError as e:
            # if the socket is simply backed up ignore the error 
            if e.errno != errno.EAGAIN: 
                self._close(e)
                return

        # when the socket buffers are full/backed up then we need to poll to see
        # when we can write again
        if result != len(buf):
            self.write = self.buffered_write
            self.write_watcher.start()
            self.write(buf[result:])

    def buffered_write(self, buf):
        """Appends a bytes like object to the transport write buffer.

        Raises BufferOverflowError if buf would cause the buffer to grow beyond
        the specified maximum.

        buf -- bytes to send

        """
        if self.closed:
            raise ConnectionClosed()

        if len(buf) + len(self.write_buffer) > self.max_size:
            raise BufferOverflowError()
        else:
            self.write_buffer.extend(buf)

    def _writtable(self, watcher, events):
        """Called by the pyev watcher (self.write_watcher) whenever the socket
        is writtable.

        Calls send using the userspace buffer (self.write_buffer) and checks
        for errors. If there are no errors then continue on as before.
        Otherwise closes the socket and calls close_cb with the error.

        """
        try:
            sent = self.sock.send(bytes(self.write_buffer))
            self.write_buffer = self.write_buffer[sent:]
            if len(self.write_buffer) == 0:
                self.write_watcher.stop()
                self.write = self.unbuffered_write
        except EnvironmentError as e:
            self._close(e)

    def _readable(self, watcher, events):
        """Called by the pyev watcher (self.read_watcher) whenever the socket
        is readable.

        Calls recv and checks for errors. If there are no errors then read_cb
        is called with the newly arrived bytes. Otherwise closes the socket
        and calls close_cb with the error.

        """
        try:
            data = self.sock.recv(4096)
            if len(data) == 0:
                self._close(ConnectionClosed())
            else:
                self.read_cb(data)
        except IOError as e:
            self._close(e)

    def _close(self, e):
        """Really close the transport with a reason.

        e -- reason the socket is being closed.

        """
        self.stop()
        self.sock.close()
        self.closed = True
        self.close_cb(e)

    def close(self):
        """Close the transport."""
        self._close(ConnectionClosed())
