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


import os
import sys
import socket
import unittest
import pyev

from whizzer import server, client, protocol
from whizzer.rpc import dispatch, proxy, msgpackrpc

from common import loop

class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.count = 0

    def tearDown(self):
        self.count = 0

    def func(self):
        self.count += 1

    def add(self, a, b):
        self.count += 1
        return a+b

    def test_add_noname(self):
        a = dispatch.Dispatch()
        a.add(self.func)
        self.assertEqual(len(a.functions), 1)
        self.assertTrue(self.func in a.functions.values())
        self.assertTrue(self.func.__name__ in a.functions.keys())

    def test_add_with_name(self):
        a = dispatch.Dispatch()
        a.add(self.func, "somebogusname")
        self.assertEqual(len(a.functions), 1)
        self.assertTrue(self.func in a.functions.values())
        self.assertTrue("somebogusname" in a.functions.keys())

    def test_call_noargs(self):
        a = dispatch.Dispatch()
        a.add(self.func)
        a.call(self.func.__name__, ())
        self.assertEqual(self.count, 1)
    
    def test_call_args(self):
        a = dispatch.Dispatch()
        a.add(self.add)
        self.assertEqual(a.call(self.add.__name__, (1, 2)), 3)
        self.assertEqual(self.count, 1)


class MockService(object):
    def __init__(self):
        self.last_called = None

    @dispatch.remote
    def add(self, a, b):
        self.last_called = self.add
        return a+b

    @dispatch.remote
    def exception(self):
        self.last_called = self.exception
        raise Exception()

    @dispatch.remote
    def rpc_error(self):
        self.last_called = self.rpc_error
        raise Exception()

    @dispatch.remote
    def tuple_ret(self, a, b, c):
        self.last_called = self.tuple_ret
        return (a,b,c) 

    @dispatch.remote
    def dict_ret(self, a, b, c):
        self.last_called = self.dict_ret
        return {'a':a,'b':b,'c':c} 

    @dispatch.remote
    def list_ret(self, a, b, c):
        self.last_called = self.list_ret
        return [a,b,c] 

    @dispatch.remote
    def not_set_future_ret(self):
        self.last_called = self.not_set_future_ret
        return future.Future()

    @dispatch.remote
    def set_future_ret(self):
        self.last_called = self.set_future_ret
        f = future.Future()
        f.set_result(True)
        return f

    def local_only(self):
        self.last_called = self.local_only
        pass

class TestMsgPackProtocol(unittest.TestCase):
    """A functional test against the msgpack rpc protocol."""
    def setUp(self):
        self.factory = msgpackrpc.MsgPackProtocolFactory(dispatch.ObjectDispatch(MockService()))
        self.protocol = self.factory.build(loop)

    def tearDown(self):
        self.factory = None
        self.protocol = None

    def runTest(self):
        unittest.TestCase.runTest(self)

    def mock_send_response(self, msgid, error, result):
        """Mock send response to make testing narrowed down and simpler."""
        self.response = (msgid, error, result)
        print "response was " + str(self.response)
    
    def test_connection_made(self):
        future_proxy = self.protocol.proxy()
        self.protocol.connection_made(None)
        self.assertTrue(isinstance(future_proxy.result(), proxy.Proxy))

    def test_handle_request(self):
        self.protocol.send_response = self.mock_send_response
        self.protocol.request(0, 0, "add", (1, 2))
        self.assertTrue(self.response == (0, None, 3))

    def test_handle_unknown_request(self):
        self.protocol.send_response = self.mock_send_response
        self.protocol.request(0, 0, "blah_add", (1, 2))
        self.assertTrue(self.response[0] == 0)
        self.assertTrue(self.response[1][0] == KeyError.__name__)
        self.assertTrue(self.response[2] == None)

    def test_handle_badargs_request(self):
        self.protocol.send_response = self.mock_send_response
        self.protocol.request(0, 0, "add", (1, 2, 3))
        self.assertTrue(self.response[0] == 0)
        self.assertTrue(self.response[1][0] == TypeError.__name__)
        self.assertTrue(self.response[2] == None)

    def test_handle_exceptioned_request(self):
        self.assertRaises(Exception, self.protocol.request, 0, 0, "exception")

    def test_handle_rpcexceptioned_request(self):
        self.protocol.send_response = self.mock_send_response
        self.protocol.request(0, 0, "rpc_error")
        self.assertTrue(self.response[1] != None)

    def test_notify(self):
        pass

    def test_unknown_notify(self):
        pass

    def test_badargs_notify(self):
        pass

    def test_exceptioned_notify(self):
        pass

    def test_rpcexceptioned_notify(self):
        pass

if __name__ == '__main__':
    unittest.main()
