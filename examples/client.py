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
import signal
import logbook
from logbook import NullHandler
from logbook.more import ColorizedStderrHandler
import pyev

sys.path.insert(0, '..')

import whizzer

logger = logbook.Logger('echo_client')


class EchoClientProtocol(whizzer.Protocol):
    def connection_made(self, address):
        """When the connection is made, send something."""
        logger.info("connection made to {}".format(address))
        self.count = 0
        self.connected = True
        self.transport.write(b'Echo Me')
        
    def data(self, data):
        logger.info("echo'd " + data.decode('ASCII'))
        if self.count < 10000:
            self.count += 1
            self.transport.write(b'Echo Me')
        else:
            self.lose_connection()
            self.connected = False

def interrupt(watcher, events):
    watcher.loop.unloop()


class EchoClient(object):
    def __init__(self, id, loop, factory):
        self.id = id
        self.loop = loop
        self.factory = factory
        self.connect_client()

    def connect_client(self):
        client = whizzer.TcpClient(self.loop, self.factory, "127.0.0.1", 2000)
        logger.info('client calling connect')
        d = client.connect()
        logger.info('client called connect')
        d.add_callback(self.connect_success)
        d.add_errback(self.connect_failed)
        self.timer = pyev.Timer(1.0, 0.0, self.loop, self.timeout, None)
        self.timer.start()

    def connect_success(self, result):
        logger.info('connect success, protocol is {}'.format(result.connected))
        self.connect_client()
        self.timer.stop()

    def connect_failed(self, error):
        logger.error('client {} connecting failed, reason {}'.format(id, error))

    def timeout(self, watcher, events):
        logger.error('timeout')

def main():
    loop = pyev.default_loop()

    signal_handler = whizzer.signal_handler(loop)

    factory = whizzer.ProtocolFactory()
    factory.protocol = EchoClientProtocol

    clients = []
    # number of parallel clients
    for x in range(0, 2):
        clients.append(EchoClient(x, loop, factory))

    signal_handler.start()
    loop.loop()

if __name__ == "__main__":
    stderr_handler = ColorizedStderrHandler(level='INFO')
    null_handler = NullHandler()
    with null_handler.applicationbound():
        with stderr_handler.applicationbound():
            main()
