import sys
sys.path.insert(0, '..')

import unittest
import pyev

from whizzer.deferred import Deferred

def print_hello():
    print("hello")

def add_nums(a, b):
    return a + b

def throw_always():
    raise Exception("success")

def keywords(a, b, **kwargs):
    return {'a':a, 'b':b, 'others':kwargs}

def add(a, b):
    return a+b

def multiply(a, b):
    return a*b

def divide(a, b):
    return a/b

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
        self.deferred = Deferred(self.logger)

    def tearDown(self):
        self.deferred = None

    def set_result(self, result):
        self.result = result

    def set_exception(self, exception):
        self.exception = exception

    def test_callback(self):
        self.deferred.add_callback(self.set_result)
        self.deferred.callback(5)
        self.assertTrue(self.result==5)

    def test_callback_chain(self):
        d = self.deferred.add_callback(add, 1)
        d.add_callback(self.set_result)
        self.deferred.callback(5)
        self.assertTrue(self.result==6)

    def test_log_error(self):
        self.deferred.add_callback(throw_always)
        self.deferred.callback()
        print(self.logger.error_msg)
        self.assertTrue(self.logger.error_msg != "")

if __name__ == '__main__':
    unittest.main()
