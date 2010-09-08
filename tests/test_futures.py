import sys
sys.path.insert(0, '..')

import unittest
import pyev

loop = pyev.default_loop()

from whizzer import futures

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
        self.executor = futures.Executor(self.loop)
        self.cb_count = 0
        self.cb_futures = []

    def test_construction(self):
        f = self.executor.submit(print_hello)
        f = self.executor.submit(add_nums, 1, 2)
        f = self.executor.submit(keywords, 1, 2, name="ev rocks")

    def test_done_result(self):
        f = self.executor.submit(add_nums, 1, 2)
        assert(f.result()==3)
        assert(f.exception()==None)

    def test_done_exception(self):
        f = self.executor.submit(throw_always)
        
        assert(isinstance(f.exception(), Exception))

        try:
            f.result()
            assert(False), "failure to reraise exception"
        except Exception as e:
            pass

    def test_future_result(self):
        f = self.executor.submit_delay(0.25, add_nums, 1, 2)
        try:
            f.result(0.1)
            raise Exception("Should have raised a TimeoutError")
        except futures.TimeoutError as e:
            pass

        assert(f.result() == 3)
        assert(f.result() == 3)
        assert(f.result(1.0) == 3)

    def test_future_exception(self):
        f = self.executor.submit_delay(0.25, throw_always)

        try:
            f.exception(0.1)
            raise Exception("Should have raised a TimeoutError")
        except futures.TimeoutError as e:
            pass

        assert(isinstance(f.exception(), Exception))
        assert(isinstance(f.exception(), Exception))
        assert(isinstance(f.exception(1.0), Exception))

    def test_future_cancel(self):
        f = self.executor.submit(add_nums, 1, 2)
        assert(f.cancel())

        try:
            f.result()()
            raise Exception("Should have raised a CancelledError")
        except futures.CancelledError as e:
            pass

        try:
            f.result()
            raise Exception("Should have raised a CancelledError")
        except futures.CancelledError as e:
            pass

        try:
            f.exception()
            raise Exception("Should have raised a CancelledError")
        except futures.CancelledError as e:
            pass

    def _callback(self, f):
        self.cb_count += 1
        self.cb_futures.append(f)

    def test_callbacks(self):
        f = self.executor.submit(add_nums, 1, 2)
        f.add_done_callback(self._callback)
        f.result()
        assert(self.cb_count == 1)
        assert(f in self.cb_futures)

if __name__ == '__main__':
    unittest.main()
