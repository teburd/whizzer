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


import signal

import pyev

from whizzer.defer import Deferred, AlreadyCalledError, CancelledError, TimeoutError
from whizzer.protocol import Protocol, ProtocolFactory
from whizzer.server import SocketServer, TcpServer, UnixServer
from whizzer.client import SocketClient, TcpClient, UnixClient
from whizzer.transport import SocketTransport, ConnectionClosed

def _interrupt(watcher, events):
    watcher.loop.unloop()

def signal_handler(loop):
    """Install a basic signal handler watcher and return it."""
    watcher = pyev.Signal(signal.SIGINT, loop, _interrupt)
    return watcher

def _perform_call(watcher, events):
    (d, method, args, kwargs) = watcher.data
    try:
        d.callback(method(*args, **kwargs))
    except Exception as e:
        d.errback(e)

def call_later(loop, logger, delay, method, *args, **kwargs):
    """Convienence method to create a timed function call."""
    d = Deferred(loop, logger=logger)
    t = pyev.Timer(delay, 0.0, loop, _perform_call, (d, method, args, kwargs))
    t.start()
    d.timer = t
    return d
