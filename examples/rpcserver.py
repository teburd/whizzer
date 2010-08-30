import sys
sys.path.insert(0, '..')

import whizzer
from whizzer import rpc
import pyev

class MyObject(object):
    def __init__(self, loop):
        self.executor = whizzer.Executor(loop)

    @rpc.remote
    def add(self, a, b):
        return a+b

    @rpc.remote
    def delayed_add(self, delay, a, b):
        return self.executor.submit_delay(delay, self.add, a, b)

if __name__ == "__main__":
    loop = pyev.default_loop()
    sighandler = whizzer.SignalHandler(loop)
    factory = rpc.RPCProtocolFactory(loop, rpc.ObjectDispatch(MyObject(loop)))
    factory.protocol = rpc.MarshalRPCProtocol
    server = whizzer.UnixServer(loop, factory, "marshal_adder")
    sighandler.register_server(server)
    loop.loop()
