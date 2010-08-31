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
import pstats
import cProfile
import pyev

sys.path.insert(0, '..')
import whizzer
from whizzer import debug

class EchoClientProtocol(whizzer.Protocol):
    def connection_made(self):
        """When the connection is made, send something."""
        self.transport.write(b'Echo Me')
        
    def data(self, data):
        #print("echo'd " + data)
        self.lose_connection()

class ClientManager(object):
    def __init__(self, loop, factory):
        self.loop = loop
        self.factory = factory
        self.timer = pyev.Timer(1.0, 0.001, loop, self.connect, factory)
        self.timer.start()

    def connect(self, watcher, events):
        client = whizzer.TcpClient(self.loop, self.factory, "127.0.0.1", 2000)
        client.connect()

if __name__ == "__main__":
    loop = pyev.default_loop()
    objwatcher = debug.ObjectWatcher(loop, [whizzer.TcpClient])
    factory = whizzer.ProtocolFactory(loop)
    factory.protocol = EchoClientProtocol
    sighandler = whizzer.SignalHandler(loop)
    cm = ClientManager(loop, factory)
    cProfile.run('loop.loop()', 'client_profile')
    pstats.Stats('client_profile').sort_stats('time').print_stats()
