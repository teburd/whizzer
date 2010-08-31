import sys
sys.path.insert(0, '..')

import whizzer
from whizzer import rpc
import pyev
import time
import cProfile
import pstats



class MyObject(object):
    def __init__(self, loop):
        self.loop = loop
        self.executor = whizzer.Executor(loop)
        self.calls = 0
        self.last = time.time()
        self.timer = pyev.Timer(1.0, 1.0, loop, self.print_stats)
        self.timer.start()

    def print_stats(self, watcher, events):
        print("Calls in the last second second " + str(self.calls))
        self.last = time.time()
        self.calls = 0

    @rpc.remote
    def add(self, a, b):
        self.calls += 1
        return a + b

    @rpc.remote
    def delayed_add(self, delay, a, b):
        self.calls += 1
        return self.executor.submit_delay(delay, self.add, a, b)

if __name__ == "__main__":
    loop = whizzer.default_loop()
    factory = rpc.RPCProtocolFactory(loop, rpc.ObjectDispatch(MyObject(loop)))
    factory.protocol = rpc.MsgPackProtocol
    server = whizzer.UnixServer(loop, factory, "msgpack_adder")
    loop.loop()
