# -*- coding: utf-8 -*-
# Copyright (c) 2010 Tom Burdick <thomas.burdick@gmail.com>
# Copyright (c) 2010 Warren Friedl <wfriedl@gmail.com>
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

import struct
from .protocol import Protocol

class LengthProtocol(Protocol):
    """Length protocol is a network encoded length number prefixed message."""

    def __init__(self, loop):
        Protocol.__init__(self, loop)
        self._buffer = bytearray()
        self._lstr = '!I'
        self._lsize = struct.calcsize(self._lstr)
        self._process = self._process_length
   
    def data(self, data):
        """Handle incoming data by buffering and then determining length
        then buffering the message.

        """
        self._buffer.extend(data)
        self._process()

    def _process_length(self):
        """Buffer until the number of bytes needed to decode to an interger
        length are available.
        
        """
        if len(self._buffer) >= self._lsize:
            self._l = struct.unpack(self._lstr, str(self._buffer[:self._lsize]))[0]
            self._buffer = self._buffer[self._lsize:]
            self._process = self._process_message
            self._process()

    def _process_message(self):
        """Buffer until the buffer is the length of the message or greater."""
        if len(self._buffer) >= self._l:
            self.message(bytes(self._buffer[:self._l]))
            self._buffer = self._buffer[self._l:]
            self._process = self._process_length
            self._process()
 
    def message(self, message):
        """Receive a message.
      
        message -- bytes like object
        
        """
        pass
            
       
    def send(self, message):
        """Send a message.

        message -- bytes like object

        """
        l = len(message)
        self.transport.write(struct.pack(self._lstr, l))
        self.transport.write(message)

