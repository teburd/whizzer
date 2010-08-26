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
        self.write = self.unbuffered_write


    def unbuffered_write(self, buf):
        """Performs an unbuffered write, the default unless socket.send does 
        not send everything, in which case an unbuffered write is done and the
        write method is set to be a buffered write until the buffer is empty
        once again.
        """
        if self.closed:
            raise ConnectionClosedError()

        result = 0
        try:
            result = self.sock.send(buf)
        except IOError as e:
            self._do_error(e)
            return
        except OSError as e:
            self._do_error(e)
            return

        if result != len(buf):
            self.write = self.buffered_write
            self.write_watcher.start()
            self.write(buf[result:])

    def buffered_write(self, buf):
        """Appends a bytes like object to the transport write buffer.

        Raises BufferOverflowError if bytes like object would cause the buffer to grow beyond the
        specified maximum.

        """
        if self.closed:
            raise ConnectionClosedError()

        if len(buf) + len(self.write_buffer) > self.max_size:
            raise BufferOverflowError()
        else:
            self.write_buffer.extend(buf)
    
    def _do_write(self, watcher, events):
        if self.closed:
            return
       
        try:
            sent = self.sock.send(bytes(buf))
            self.write_buffer = self.write_buffer[written:]
            if len(self.write_buffer) == 0:
                self.write_watcher.stop()
                self.write = self.unbuffered_write
        except IOError as e:
            self._do_error(e)
        except OSError as e:
            self._do_error(e)

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


