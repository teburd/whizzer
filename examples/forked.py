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

import time
import signal

import logbook
from logbook import NullHandler
from logbook.more import ColorizedStderrHandler

import pyev

from whizzer.process import Process
from whizzer.server import UnixServer
from whizzer.client import UnixClient
from whizzer.rpc.dispatch import remote, ObjectDispatch
from whizzer.rpc.picklerpc import  PickleProtocolFactory
from whizzer.rpc.msgpackrpc import MsgPackProtocolFactory

logger = logbook.Logger('forked!')


class AdderService(object):
    def __init__(self):
        logger.info('creating an adder service')

    @remote
    def add(self, a, b):
        return a+b

def server_stop(watcher, events):
    logger.debug('got shutdown')
    watcher.loop.unloop(pyev.EVUNLOOP_ALL)

def server_main(loop, path):
    """Run in the client after the fork."""
    loop.fork()
    logger.debug('forked function')
    sigintwatcher = pyev.Signal(signal.SIGINT, loop, lambda watcher, events: logger.info('interrupt ignored'))
    sigintwatcher.start()
    sigtermwatcher = pyev.Signal(signal.SIGTERM, loop, server_stop)
    sigtermwatcher.start()
    adder = AdderService()
    dispatcher = ObjectDispatch(adder)
    pickle_factory = PickleProtocolFactory(dispatcher)
    pickle_server = UnixServer(loop, pickle_factory, path)
    pickle_server.start()
    msgpack_factory = MsgPackProtocolFactory(dispatcher)
    msgpack_server = UnixServer(loop, msgpack_factory, path + '_mp')
    msgpack_server.start()

    logger.debug('running server loop')

    loop.loop()

    logger.debug('server unlooped')


def main():
    path = 'adder_socket'
    loop = pyev.default_loop()

    sigwatcher = pyev.Signal(signal.SIGINT, loop, lambda watcher, events: watcher.loop.unloop(pyev.EVUNLOOP_ALL))
    sigwatcher.start()
    
    p = Process(loop, server_main, loop, 'adder_socket')
    p.start()

    pickle_factory = PickleProtocolFactory()
    pickle_client = UnixClient(loop, pickle_factory, path)

    retries = 10 
    while retries:
        try:
            pickle_client.connect().result()
            retries = 0
        except Exception as e:
            time.sleep(0.1)
            retries -= 1

    proxy = pickle_factory.proxy(0).result()
    
    start = time.time()
    s = 0
    for i in range(10000):
        s = proxy.call('add', 1, s)
    stop = time.time()

    logger.info('pickle-rpc took {} seconds to perform {} calls, {} calls per second', stop-start, s, s/(stop-start))

    start = time.time()
    for i in range(10000):
        proxy.notify('add', 1, s)
    proxy.call('add', 1, s)
    stop = time.time()

    logger.info('pickle-rpc took {} seconds to perform {} notifications, {} notifies per second', stop-start, 10000, 10000/(stop-start))

    msgpack_factory = MsgPackProtocolFactory()
    msgpack_client = UnixClient(loop, msgpack_factory, path + '_mp')

    retries = 10 
    while retries:
        try:
            msgpack_client.connect().result()
            retries = 0
        except Exception as e:
            time.sleep(0.1)
            retries -= 1

    proxy = msgpack_factory.proxy(0).result()
    
    start = time.time()
    s = 0
    for i in range(10000):
        s = proxy.call('add', 1, s)
    stop = time.time()

    logger.info('msgpack-rpc took {} seconds to perform {} calls, {} calls per second', stop-start, s, s/(stop-start))

    start = time.time()
    for i in range(10000):
        proxy.notify('add', 1, s)
    proxy.call('add', 1, s)
    stop = time.time()

    logger.info('msgpack-rpc took {} seconds to perform {} notifications, {} notifies per second', stop-start, 10000, 10000/(stop-start))

    p.stop()

if __name__ == "__main__":
    stderr_handler = ColorizedStderrHandler(level='DEBUG')
    null_handler = NullHandler()
    with null_handler.applicationbound():
        with stderr_handler.applicationbound():
            main()
