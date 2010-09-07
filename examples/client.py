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
    def __init__(self, loop, manager):
        whizzer.Protocol.__init__(self, loop)
        self.manager = manager

    def connection_made(self):
        """When the connection is made, send something."""
        self.transport.write(b'Echo Me')
        
    def data(self, data):
        #print("echo'd " + data)
        self.lose_connection()

    def connection_lost(self, reason=None):
        self.manager.lost_connection(self)
        self.manager = None

class ClientFactory(whizzer.ProtocolFactory):
    def __init__(self, loop, manager):
        whizzer.ProtocolFactory.__init__(self, loop)
        self.manager = manager
        self.protocol = EchoClientProtocol

    def build(self):
        return self.protocol(self.loop, self.manager)


class ClientManager(object):
    def __init__(self, loop):
        self.loop = loop
        self.factory = ClientFactory(loop, self)
        self.clients = set()
        self.timer = pyev.Timer(1.0, 0.001, loop, self.connect, self.factory)
        self.timer.start()

    def connect(self, watcher, events):
        client = whizzer.TcpClient(self.loop, self.factory, "127.0.0.1", 2000)
        client.connect()
        self.clients.add(client)

    def lost_connection(self, client):
        self.clients.remove(client)

if __name__ == "__main__":
    loop = pyev.default_loop()
    sighandler = whizzer.SignalHandler(loop)
    cm = ClientManager(loop)
    cProfile.run('loop.loop()', 'client_profile')
    pstats.Stats('client_profile').sort_stats('time').print_stats()
