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

import sys
import time
import signal
import logbook
from logbook.more import ColorizedStderrHandler

import pyev

sys.path.insert(0, '..')

import whizzer
from whizzer import protocol

logger = logbook.Logger('echo server')


class EchoProtocolFactory(protocol.ProtocolFactory):
    def __init__(self):
        self.echoes = 0

    def build(self, loop):
        return EchoProtocol(loop, self)


class EchoProtocol(protocol.Protocol):
    def __init__(self, loop, factory):
        self.loop = loop
        self.factory = factory

    def data(self, data):
        self.transport.write(data)
        self.factory.echoes += 1

class EchoStatistics(object):
    def __init__(self, loop, factory):
        self.loop = loop
        self.factory = factory
        self.timer = pyev.Timer(2.0, 2.0, loop, self._print_stats)
    
    def start(self):
        self.timer.start()

    def _print_stats(self, watcher, events):
        logger.error('echoes per seconds {}'.format(self.factory.echoes/2.0))
        self.factory.echoes = 0

def main():
    loop = pyev.default_loop()
    
    signal_handler = whizzer.signal_handler(loop)
    signal_handler.start()
    
    factory = EchoProtocolFactory()
    server = whizzer.TcpServer(loop, factory, "127.0.0.1", 2000, 256)
    stats = EchoStatistics(loop, factory)

    signal_handler.start()
    server.start()
    stats.start()

    loop.loop()

if __name__ == "__main__":
    stderr_handler = ColorizedStderrHandler(level='DEBUG')
    with stderr_handler.applicationbound():
        main()
