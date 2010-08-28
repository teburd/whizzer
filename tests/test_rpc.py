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

sys.path.insert(0, "..")

from whizzer import server, client, errors, protocol, rpc

loop = pyev.default_loop()

class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.count = 0

    def tearDown(self):
        self.count = 0

    def func(self):
        self.count += 1

    def test_add_noname(self):
        a = rpc.Dispatch()
        a.add(self.func)
        self.assertEqual(len(a.methods), 1)
        self.assertTrue(self.func in a.methods.values())
        self.assertTrue(self.func.__name__ in a.methods.keys())

    def test_add_with_name(self):
        a = rpc.Dispatch()
        a.add(self.func, "somebogusname")
        self.assertEqual(len(a.methods), 1)
        self.assertTrue(self.func in a.methods.values())
        self.assertTrue("somebogusname" in a.methods.keys())