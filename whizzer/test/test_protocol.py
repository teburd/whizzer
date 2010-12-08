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
import unittest
import pyev

from whizzer.protocol import Protocol, ProtocolFactory
from mocks import *
from common import loop

class TestProtocol(unittest.TestCase):
    def test_protocol(self):
        protocol = Protocol(loop) 
    
    def test_factory(self):
        factory = ProtocolFactory()

    def test_factory_build(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        p = factory.build(loop)
        self.assertTrue(isinstance(p, Protocol))

    def test_lose_connection(self):
        factory = ProtocolFactory()
        factory.protocol = Protocol
        p = factory.build(loop)
        self.assertTrue(isinstance(p, Protocol))
        t = MockTransport()
        p.make_connection(t, 'test')
        p.lose_connection()
        self.assertTrue(t.closes==1)
        


if __name__ == '__main__':
    unittest.main()
