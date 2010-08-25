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

import pyev

sys.path.insert(0, '..')

import whizzer

last = time.time()
count = 0

class EchoProtocol(whizzer.Protocol):
    def data(self, data):
        global count
        count += 1
        self.transport.write(data)

def statistics(watcher, events):
    global count
    global last
    diff = time.time() - last
    eps = count/diff
    print("echos per second " + str(eps))
    last = time.time()
    count = 0
    
    

if __name__ == "__main__":
    loop = pyev.default_loop()
    sighandler = whizzer.SignalHandler(loop)
    factory = whizzer.ProtocolFactory(loop)
    factory.protocol = EchoProtocol
    server = whizzer.TcpServer(loop, factory, "127.0.0.1", 2000)
    sighandler.register_server(server)

    stats_watcher = pyev.Timer(2.0, 2.0, loop, statistics)
    stats_watcher.start()

    loop.loop()
