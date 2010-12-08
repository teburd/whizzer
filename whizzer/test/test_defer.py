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

import unittest
import pyev

from whizzer.defer import Deferred, CancelledError, AlreadyCalledError, TimeoutError

from common import loop

def throw_always(result):
    raise Exception("success")

def one_always(result):
    return 1

def add(a, b):
    return a+b

class TestDeferred(unittest.TestCase):
    def setUp(self):
        self.deferred = Deferred(loop)
        self.result = None

    def tearDown(self):
        self.deferred = None
        self.result = None

    def set_result(self, result):
        self.result = result

    def set_exception(self, exception):
        self.exception = exception

    def call_later(self, delay, func, *args, **kwargs):
        timer = pyev.Timer(delay, 0.0, loop, self._do_later, (func, args, kwargs))
        timer.start()
        return timer

    def _do_later(self, watcher, events):
        (func, args, kwargs) = watcher.data
        func(*args, **kwargs)
        watcher.stop()

    def test_callback(self):
        self.deferred.add_callback(self.set_result)
        self.deferred.callback(5)
        self.assertTrue(self.result==5)

    def test_callback_chain(self):
        d = self.deferred
        d.add_callback(add, 1)
        d.add_callback(self.set_result)
        self.deferred.callback(5)
        self.assertTrue(self.result==6)

    def test_log_error(self):
        """Unhandled exceptions should be logged if the deferred is deleted."""
        self.deferred.add_callback(throw_always)
        self.deferred.callback(None)
        self.deferred = None # delete it

    def test_errback(self):
        self.deferred.add_errback(self.set_result)
        self.deferred.errback(Exception())
        self.assertTrue(isinstance(self.result, Exception))

    def test_callback_skips(self):
        """When a callback raises an exception
        all callbacks without errbacks are skipped until the next
        errback is found.

        """
        self.deferred.add_callback(throw_always)
        self.deferred.add_callback(one_always)
        self.deferred.add_callback(add, 2)
        self.deferred.add_errback(one_always)
        self.deferred.add_callback(self.set_result)
        self.deferred.callback(None)
        self.assertTrue(self.result==1)

    def test_errback_reraised(self):
        """If an errback raises, then the next errback is called."""
        self.deferred.add_errback(throw_always)
        self.deferred.add_errback(self.set_result)
        self.deferred.errback(Exception())
        self.assertTrue(isinstance(self.result, Exception))

    def test_cancelled(self):
        self.deferred.cancel()
        self.assertRaises(CancelledError, self.deferred.errback, Exception("testcancelled"))
        self.assertRaises(CancelledError, self.deferred.callback, None)
        self.assertRaises(CancelledError, self.deferred.result)

    def test_already_called(self):
        self.deferred.callback(None)
        self.assertRaises(AlreadyCalledError, self.deferred.errback, Exception("testalreadycalled"))
        self.assertRaises(AlreadyCalledError, self.deferred.callback, None)
        self.assertRaises(AlreadyCalledError, self.deferred.cancel)

    def test_cancel_callback(self):
        self.deferred = Deferred(loop, cancelled_cb=self.set_result)
        self.deferred.cancel()
        self.assertTrue(self.result == self.deferred)

    def test_result_chain(self):
        self.deferred.callback(5)
        self.assertTrue(self.deferred.result()==5)
        self.deferred.add_callback(add, 2)
        self.assertTrue(self.deferred.result()==7)
        self.deferred.add_callback(throw_always)
        self.assertRaises(Exception, self.deferred.result)

    def test_result(self):
        self.deferred.callback(5)
        self.assertTrue(self.deferred.result()==5)

    def test_result_exceptioned(self):
        self.deferred.errback(Exception("exceptioned result"))
        self.assertRaises(Exception, self.deferred.result)

    def test_delayed_result(self):
        now = time.time()
        t1 = self.call_later(0.5, self.deferred.callback, 5)
        self.assertTrue(self.deferred.result() == 5)
        self.assertTrue(time.time() - now > 0.4)

    def test_delayed_result_chained(self):
        now = time.time()
        t1 = self.call_later(0.5, self.deferred.callback, 5)
        self.deferred.add_callback(add, 4)
        self.assertTrue(self.deferred.result() == 9)
        self.assertTrue(time.time() - now > 0.4)

    def test_delayed_result_timeout(self):
        t1 = self.call_later(0.5, self.deferred.callback, 5)
        self.assertRaises(TimeoutError, self.deferred.result, 0.1)

    def test_delayed_result_cancelled(self):
        t1 = self.call_later(0.5, self.deferred.callback, 5)
        t2 = self.call_later(0.2, self.deferred.cancel)
        self.assertRaises(CancelledError, self.deferred.result, 0.3)

if __name__ == '__main__':
    unittest.main()
