import sys
sys.path.insert(0, '..')

import unittest
import pyev

loop = pyev.default_loop()

from whizzer.defer import Deferred, CancelledError, AlreadyCalledError, TimeoutError

def throw_always(result):
    raise Exception("success")

def one_always(result):
    return 1

def add(a, b):
    return a+b

class FakeLogger(object):
    def __init__(self):
        self.info_msg = ""
        self.debug_msg = ""
        self.warn_msg = ""
        self.error_msg = ""

    def info(self, msg):
        self.info_msg = msg

    def debug(self, msg):
        self.debug_msg = msg

    def warn(self, msg):
        self.warn_msg = msg
 
    def error(self, msg):
        self.error_msg = msg

class TestDeferred(unittest.TestCase):
    def setUp(self):
        self.logger = FakeLogger()
        self.deferred = Deferred(loop, logger=self.logger)
        self.result = None

    def tearDown(self):
        self.deferred = None
        self.result = None

    def set_result(self, result):
        self.result = result

    def set_exception(self, exception):
        self.exception = exception

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
        self.assertTrue(self.logger.error_msg != "")

    def test_errback(self):
        self.deferred.add_errback(self.set_result)
        self.deferred.errback(5)
        self.assertTrue(self.result==5)

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
        self.deferred.errback(None)
        self.assertTrue(isinstance(self.result, Exception))

    def test_cancelled(self):
        self.deferred.cancel()
        self.assertRaises(CancelledError, self.deferred.errback, None)
        self.assertRaises(CancelledError, self.deferred.callback, None)

    def test_already_called(self):
        self.deferred.callback(None)
        self.assertRaises(AlreadyCalledError, self.deferred.errback, None)
        self.assertRaises(AlreadyCalledError, self.deferred.callback, None)

    def test_cancel_callback(self):
        self.deferred = Deferred(loop, cancelled_cb=self.set_result)
        self.deferred.cancel()
        self.assertTrue(self.result == self.deferred)

    def test_last(self):
        self.deferred.callback(5)
        self.assertTrue(self.deferred.last()==5)
        self.deferred.add_callback(add, 2)
        self.assertTrue(self.deferred.last()==7)
        self.deferred.add_callback(throw_always)
        self.assertRaises(Exception, self.deferred.last)

    def test_first(self):
        self.deferred.callback(5)
        self.assertTrue(self.deferred.first()==5)

    def test_first_exceptioned(self):
        self.deferred.errback(Exception)
        self.assertRaises(Exception, self.deferred.first)

if __name__ == '__main__':
    unittest.main()
