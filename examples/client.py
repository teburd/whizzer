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
import logbook
import pyev

sys.path.insert(0, '..')

import whizzer


logger = logbook.Logger('echo_client')

class EchoClientProtocol(whizzer.Protocol):
    def connection_made(self):
        """When the connection is made, send something."""
        print("connection made")
        self.transport.write(b'Echo Me')
        
    def data(self, data):
        print("echo'd " + data.decode('ASCII'))
        self.lose_connection()

def interrupt(watcher, events):
    watcher.loop.unloop()


class Client(object):
    count = 0
    def __init__(self, loop, factory):
        Client.count += 1
        self.logger = logbook.Logger('client {}'.format(Client.count))
        self.loop = loop
        self.factory = factory
        self.client = None
        self.connect()

    def connect(self):
        self.client = whizzer.TcpClient(self.loop, self.factory, "127.0.0.1",
            2000, logger=self.logger)
        d = self.client.connect()
        d.add_callback(self.connected)
        d.add_errback(self.disconnected)

    def connected(self, result):
        logger.info('connected')
        self.timer = pyev.Timer(0.001, 0.0, self.loop,
            lambda watcher, event: self.connect())
        self.timer.start()

    def disconnected(self, result):
        logger.error('failed to connect')
        self.timer = pyev.Timer(0.001, 0.0, self.loop,
            lambda watcher, event: self.connect())
        self.timer.start()


def main():
    loop = pyev.default_loop()

    signal_handler = whizzer.signal_handler(loop)

    factory = whizzer.ProtocolFactory()
    factory.protocol = EchoClientProtocol

    clients = []
    for x in range(0, 100):
        clients.append(Client(loop, factory)) 

    signal_handler.start()
    loop.loop()

if __name__ == "__main__":
    from logbook.more import ColorizedStderrHandler
    h = ColorizedStderrHandler(level='DEBUG')

    with h.applicationbound():
        main()
