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
import pyev

sys.path.insert(0, '..')
import whizzer
from whizzer import rpc

if __name__ == "__main__":
    loop = pyev.default_loop()
    factory = rpc.RPCProtocolFactory(loop)
    factory.protocol = rpc.MarshalRPCProtocol
    sighandler = whizzer.SignalHandler(loop)
    client = whizzer.UnixClient(loop, factory, "marshal_adder")
    client.connect()
    proxy = factory.proxy(0).result()
    print proxy.call("add", 2, 3)
    proxy.set_timeout(5.0)

    f1 = proxy.begin_call("add", 5, 4)
    f2 = proxy.begin_call("add", 7, 12)
    f3 = proxy.begin_call("add", 5, 500)
    f4 = proxy.begin_call("delayed_add", 3.0, 500, 500)

    print f3.result()
    print f2.result()
    print f1.result()
    print f4.result()

    t = timeit.Timer('proxy.call("add", 2, 3)', 'from __main__ import proxy')
    r = t.timeit(10000)
    print "Calls per second: %f" % (10000.0/r)
    t = timeit.Timer('proxy.notify("add", 2, 3)', 'from __main__ import proxy')
    t = t.timeit(10000)
    print "Notifies per second: %f" %(10000.0/t)
