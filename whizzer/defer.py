# -*- coding: utf-8 -*-
# Copyright (c) 2010 Tom Burdick <thomas.burdick@gmail.com>
# Copyright (c) 2001-2010 Twisted Matrix Laboratories
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

import logging

"""An implementation of Twisted Deferred class and helpers with some add ons
that make Deferred also look similiar to pythonfutures.Future object.

It attempts to make writting callback oriented or serial coroutine style
relatively easy to write.

"""

class AlreadyCalledError(Exception):
    """Error raised if a Deferred has already had errback or callback called."""

class LastException(object):
    """When this object dies if there is something set to self.exception a string
    representation of it is printed out upon deletion.

    """
    def __init__(self):
        self.exception = None

    def __del__(self):
        if self.exception:
            logging.err(str(self.exception))
            

class Deferred(object):
    """Deferred result handling.

    Follows the Twisted Deferred interface with the exception of camel case.

    It also requires a pyev loop be passed to the constructor.

    """

    def __init__(self, loop):
        """Deferred.

        loop -- a pyev loop instance

        """
        self.loop = loop
        self.called = False
        self._result = None
        self._exception = None
        self._callbacks = []
        self._current = 0

    def add_callbacks(self, callback, errback=None, callback_args=None,
                      callback_kwargs=None, errback_args=None,
                      errback_kwargs=None):
        """Add a callback and errback to the callback chain.

        If the previous callback succeeds the return value is passed as the
        first argument to the next callback in the chain.

        If the previous callback raises an exception the exception is passed as
        the first argument to the next errback in the chain.
        
        """
        self._callbacks.append((callback, errback, callback_args,
                               callback_kwargs, errback_args,
                               errback_kwargs))

        if self.called:
            self._run_callbacks()

    def add_callback(self, callback, *callback_args, **callback_kwargs):
        """Add a callback without an associated errback."""
        self.add_callbacks(callback, callback_args=callback_args,
                           callback_kwargs=callback_kwargs)

    def add_errback(self, errback, *errback_args, **errback_kwargs):
        """Add a errback without an associated callback."""
        self.add_callbacks(None, errback=errback, errback_args=errback_args,
                           errback_kwargs=errback_kwargs)

    def callback(self, result):
        """Begin the callback chain with the first callback."""
        self._start_callbacks(result, None)

    def errback(self, exception):
        self._start_callbacks(None, exception)

    def result(self, timeout=None):
        """Return the result or raise the exception first given to callback()
        or errback().
        
        This will block until the result is available or raise a TimeoutError
        given a timeout.

        """
        if self._exception:
            raise self._exception
        else:
            return self._result


    def final_result(self, timeout=None):
        """Return the last result of the callback chain or raise the last
        exception thrown and not caught by an errback.

        This will block until the result is available or raise a TimeoutError
        given a timeout.

        This acts much like a pythonfutures.Future.result() call
        except the entire callback processing chain is performed first.

        """
        if self._exception:
            raise self._exception
        else:
            return self._result

    def _start_callbacks(self, result, exception):
        """Perform the callback chain going back and forth between the callback
        and errback as needed.

        If an exception is raised and the entire chain is gone through without a valid
        errback then its simply logged.

        """
        self._result = result
        self._exception = exception

    def _run_callbacks(self):
        while self.callbacks:
            cb, eb, cb_args, cb_kwargs, eb_args, eb_kwargs = self._callbacks.pop(0)
            if cb and not self.exception:
                try:
                    self.result = cb(result, *cb_args, **cb_kwargs)
                except Exception as e:
                    self.exception = e
            elif eb and self.exception:
                try:
                    self.result = eb(error, *cb_args, **cb_kwargs)
                    self.exception = None
                except Exception as e:
                    self.exception = e

