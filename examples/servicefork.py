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


""" This example starts up an adder service and 4 adder clients that are themselves
benchmarking sevices (which can have bench_notify remotely called)

At the moment the benchmarking services simply do 1000 notifies and a single
rpc call every second or so, you can easily modify this to really push the
adder service on your machine to see what is possible.

"""



import sys
import signal
import time

import pyev

sys.path.insert(0, '..')

from whizzer.rpc.dispatch import remote
from whizzer.rpc.service import Service, ServiceProxy, spawn


class Adder(Service):
    
    def stats_init(self):
        self.add_calls = 0
        self.last_stats = time.time()
        self.stats_timer = pyev.Timer(2.0, 2.0, self.loop, self.stats)
        self.stats_timer.start()

    def stats(self, watcher, events):
        diff = time.time() - self.last_stats
        self.logger.info("{} calls in {} seconds, {} calls per second".format(
            self.add_calls, diff, self.add_calls/diff))
        self.add_calls = 0
        self.last_stats = time.time()

    def run(self):
        self.signal_init()
        self.listen_init()
        self.stats_init()
        self.logger.info("starting")
        self.loop.start()

    @remote
    def add(self, a, b):
        self.add_calls += 1
        return a+b


class AdderBench(Service):
    def __init__(self, loop, name, path, adder_path):
        Service.__init__(self, loop, name, path)
        self.adder_path = adder_path

    def stats_init(self):
        self.add_calls = 0
        self.last_stats = time.time()
        self.stats_timer = pyev.Timer(2.0, 2.0, self.loop, self.stats)
        self.stats_timer.start()

    def stats(self, watcher, events):
        self.bench_notify(20000)
        diff = time.time() - self.last_stats
        #self.logger.info("{} calls in {} seconds, {} calls per second".format(
        #            self.add_calls, diff, self.add_calls/diff))
        self.add_calls = 0
        self.last_stats = time.time()

    def proxy_init(self):
        self.proxy = ServiceProxy(self.loop, self.adder_path)
        connected = False
        while not connected:
            try:
                self.proxy.connect().result()
                connected = True
            except:
                time.sleep(0.1)

    def run(self):
        self.signal_init()
        self.listen_init()
        self.stats_init()
        self.proxy_init()
        self.logger.info("starting")
        self.loop.start()

    @remote
    def bench_notify(self, calls):
        #self.logger.info("notify")
        start = time.time()
        for x in range(calls):
            self.proxy.notify('add', 1, 1)
        self.proxy.call('add', 1, 1)
        end = time.time()
        #self.logger.info("took {} to perform {} notifies, {} notifies per second".format(
        #    end-start, calls, calls/(end-start)))


def main():
    path = "adder_service"
    name = "adder"

    loop = pyev.default_loop()

    sigwatcher = pyev.Signal(signal.SIGINT, loop, lambda watcher, events: watcher.loop.stop(pyev.EVBREAK_ALL))
    sigwatcher.start()

    service = spawn(Adder, loop, name, path)
    sproxy = ServiceProxy(loop, path)

    sproxy.connect()

    clients = []
    proxies = []

    # to push the server further (to see how fast it will really go...)
    # just add more clients!
    for x in range(20):
        bpath = "adder_bench_{}".format(x)
        client = spawn(AdderBench, loop, bpath, bpath, path)
        bproxy = ServiceProxy(loop, "adder_bench_1")
        bproxy.connect()
        clients.append(client)
        proxies.append(bproxy)

    loop.start()

if __name__ == "__main__":
    main()
