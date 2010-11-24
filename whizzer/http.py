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

import logbook
import pyev

from io import BytesIO

from whizzer.protocol import Protocol, ProtocolFactory

logger = logbook.Logger(__name__)

class HTTPProtocol(Protocol):
    def __init__(self):
        self.input_buffer = StringIO()
        self._process = self._request

    def data(self, data):
        self.input_buffer.write(data)
        lines = self.input_buffer.getvalue().split('\r\n')
        if len(lines) > 0:
            for line in lines:
                logger.debug('got line: {}'.format(line))
                self._process(line)
            self.input_buffer = BytesIO(self.lines[len(self.lines) - 1])


    def _process(self, line):
        """State machine transition method.

        HTTPProtocol acts as a state machine where
        this function is aliased to handle the transition to the next possible
        set of states.

        """

    def _request_line(self, line):
        """Handle the request line."""


