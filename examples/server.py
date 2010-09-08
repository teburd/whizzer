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
import logging

import pyev
import cProfile
import pstats

sys.path.insert(0, '..')

import whizzer

class EchoProtocol(whizzer.Protocol):
    def data(self, data):
        print "got data, returning it"
        self.transport.write(data)

if __name__ == "__main__":
    loop = pyev.default_loop()
    
    logger = logging.getLogger('echo_server')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    signal_handler = whizzer.SignalHandler(loop)
   
    factory = whizzer.ProtocolFactory()
    factory.protocol = EchoProtocol

    server = whizzer.TcpServer(loop, factory, "127.0.0.1", 2000, logger=logger)
    server.start()
    
    loop.loop()
