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
import unittest
import pyev

sys.path.insert(0, "..")

from whizzer import futures

loop = pyev.default_loop()

def print_hello():
    print("hello")

def add_nums(a, b):
    return a + b

def throw_always():
    raise Exception("success")

def keywords(a, b, **kwargs):
    return {'a':a, 'b':b, 'others':kwargs}

class TestFuture(unittest.TestCase):
    count = 0
    def setUp(self):
        global loop
        self.loop = loop
        self.cb_count = 0
        self.cb_futures = []

    def tearDown(self):
        pass

    def test_construction(self):
        f = futures.Future(self.loop, print_hello)
        f = futures.Future(self.loop, add_nums, 1, 2)
        f = futures.Future(self.loop, keywords, 1, 2, name="ev rocks")

    def test_perform(self):
        f = futures.Future(self.loop, print_hello)
        self.assertTrue(f.perform())

    def test_done_result(self):
        f = futures.Future(self.loop, add_nums, 1, 2)
        f.perform()
        self.assertEqual(f.result(), 3)
        self.assertEqual(f.exception(), None)

    def test_done_exception(self):
        f = futures.Future(self.loop, throw_always)
        f.perform()

        self.assertTrue(isinstance(f.exception(), Exception))

        self.assertRaises(Exception, f.result)

    def test_future_result(self):
        f = futures.Future(self.loop, add_nums, 1, 2)
        t = pyev.Timer(2.0, 0.0, self.loop, lambda watcher, events: f.perform())
        t.start()

        self.assertRaises(futures.TimeoutError, f.result, 0.5)
        self.assertEqual(f.result(), 3)
        self.assertEqual(f.result(), 3)
        self.assertEqual(f.result(1.0), 3)

    def test_future_exception(self):
        f = futures.Future(self.loop, throw_always)
        t = pyev.Timer(2.0, 0.0, self.loop, lambda watcher, events: f.perform())
        t.start()

        self.assertRaises(futures.TimeoutError, f.exception, 0.5)

        self.assertTrue(isinstance(f.exception(), Exception))
        self.assertTrue(isinstance(f.exception(), Exception))
        self.assertTrue(isinstance(f.exception(1.0), Exception))

    def test_future_cancel(self):
        f = futures.Future(self.loop, add_nums, 1, 2)

        self.assertTrue(f.cancel())

        self.assertRaises(futures.CancelledError, f.result)

        self.assertRaises(futures.CancelledError, f.exception)

    def _callback(self, f):
        self.cb_count += 1
        self.cb_futures.append(f)

    def test_callbacks(self):
        f = futures.Future(self.loop, add_nums, 1, 2)
        f.add_done_callback(self._callback)
        f.perform()
        self.assertEqual(self.cb_count, 1)
        self.assertTrue(f in self.cb_futures)

if __name__ == '__main__':
    unittest.main()
