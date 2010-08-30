import sys
sys.path.insert(0, '..')

import whizzer
from whizzer import rpc
import pyev

class MyObject(object):
    @rpc.remote
    def add(self, a, b):
        print type(a)
        print type(b)
        return a+b

if __name__ == "__main__":
    loop = pyev.default_loop()
    sighandler = whizzer.SignalHandler(loop)
    factory = rpc.RPCProtocolFactory(loop, rpc.ObjectDispatch(MyObject()))
    factory.protocol = rpc.MarshalRPCProtocol
    server = whizzer.UnixServer(loop, factory, "marshal_adder")
    sighandler.register_server(server)
    loop.loop()
