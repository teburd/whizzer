# -*- coding: utf-8 -*-
# Copyright (c) 2010 Tom Burdick <thomas.burdick@gmail.com>
# Copyright (c) 2001-2010 
# Allen Short
# Andy Gayton
# Andrew Bennetts
# Antoine Pitrou
# Apple Computer, Inc.
# Benjamin Bruheim
# Bob Ippolito
# Canonical Limited
# Christopher Armstrong
# David Reid
# Donovan Preston
# Eric Mangold
# Eyal Lotem
# Itamar Shtull-Trauring
# James Knight
# Jason A. Mobarak
# Jean-Paul Calderone
# Jessica McKellar
# Jonathan Jacobs
# Jonathan Lange
# Jonathan D. Simms
# Jürgen Hermann
# Kevin Horn
# Kevin Turner
# Mary Gardiner
# Matthew Lefkowitz
# Massachusetts Institute of Technology
# Moshe Zadka
# Paul Swartz
# Pavel Pergamenshchik
# Ralph Meijer
# Sean Riley
# Software Freedom Conservancy
# Travis B. Hartwell
# Thijs Triemstra
# Thomas Herve
# Timothy Allen
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

import traceback
import signal
import sys
import collections
import logbook
import pyev

logger = logbook.Logger(__name__)

"""An implementation of Twisted Deferred class and helpers with some add ons
that make Deferred also look similiar to pythonfutures.Future object.

It attempts to make writting callback oriented or serial coroutine style
relatively easy to write.

"""


class AlreadyCalledError(Exception):
    """Error raised if a Deferred has already had errback or callback called."""


class TimeoutError(Exception):
    """Error raised if a Deferred first(), every(), or final() call timeout."""


class CancelledError(Exception):
    """Error raised if a Deferred first(), every(), or final() call timeout."""


class LastException(object):
    """When this object dies if there is something set to self.exception a
    traceback is printed.

    The reason this object exists is that printing the stacktrace before a
    deferred is deleted is incorrect. An errback can be added at any time
    that would then trap the exception. So until the Deferred is collected
    the only sane thing to do is nothing.
    
    """
    def __init__(self):
        """LastException.

        logger -- optional logger object, excepted to have an error method.

        """
        self.exception = None
        self.tb_info = None

    def __del__(self):
        if self.exception:

            logger.error("Unhandled Exception " + str(self.exception) + " of type " + str(type(self.exception)))
            if self.tb_info:
                logger.error("Traceback: \n" + str(self.tb_info))
            else:
                logger.error("Traceback: Unavailable")

        self.exception = None
        self.tb_info = None


class Deferred(object):
    """Deferred result handling.

    Follows the Twisted Deferred interface with the exception of camel case.

    """

    warnings = False

    def __init__(self, loop, cancelled_cb=None):
        """Deferred.

        loop -- a pyev loop instance
        cancelled_cb -- an optional callable given this deferred as its
                        argument when cancel() is called.

        """
        self.loop = loop
        self.called = False
        self._done = False
        self._cancelled = False
        self._cancelled_cb = cancelled_cb
        self._wait = False
        self._result = None
        self._exception = False
        self._tb_info = None
        self._callbacks = collections.deque()
        self._last_exception = LastException()

    def add_callbacks(self, callback, errback=None, callback_args=None,
                      callback_kwargs=None, errback_args=None,
                      errback_kwargs=None):
        """Add a callback and errback to the callback chain.

        If the previous callback succeeds the return value is passed as the
        first argument to the next callback in the chain.

        If the previous callback raises an exception the exception is passed as
        the first argument to the next errback in the chain.
        
        """
        self._callbacks.appendleft((callback, errback, callback_args,
                               callback_kwargs, errback_args,
                               errback_kwargs))

        if self.called:
            self._do_callbacks()

        return self

    def add_callback(self, callback, *callback_args, **callback_kwargs):
        """Add a callback without an associated errback."""
        return self.add_callbacks(callback, callback_args=callback_args,
                           callback_kwargs=callback_kwargs)

    def add_errback(self, errback, *errback_args, **errback_kwargs):
        """Add a errback without an associated callback."""
        return self.add_callbacks(None, errback=errback, errback_args=errback_args,
                           errback_kwargs=errback_kwargs)

    def callback(self, result):
        """Begin the callback chain with the first callback."""
        self._start_callbacks(result, False)

    def errback(self, result):
        """Begin the callback chain with the first errback.

        result -- A BaseException derivative.

        """

        assert(isinstance(result, BaseException))
        self._start_callbacks(result, True)

    def result(self, timeout=None):
        """Return the last result of the callback chain or raise the last
        exception thrown and not caught by an errback.

        This will block until the result is available.
        
        If a timeout is given and the call times out raise a TimeoutError

        If SIGINT is caught while waiting raises CancelledError.

        If cancelled while waiting raises CancelledError

        This acts much like a pythonfutures.Future.result() call
        except the entire callback processing chain is performed first.

        """

        self._do_wait(timeout)

        if self._exception:
            self._last_exception.exception = None
            self._last_exception.tb_info = None
            raise self._result
        else:
            return self._result

    def cancel(self):
        """Cancel the deferred."""
        if self.called:
            raise AlreadyCalledError()
        self._cancel()

    def _cancel(self):
        if not self._cancelled:
            self._cancelled = True
            if self._cancelled_cb:
                self._cancelled_cb(self)
    
    def _clear_wait(self, watcher, events):
        """Clear the wait flag if an interrupt is caught."""
        self._wait = False

    def _do_wait(self, timeout):
        """Wait for the deferred to be completed for a period of time

        Raises TimeoutError if the wait times out before the future is done.
        Raises CancelledError if the future is cancelled before the
        timeout is done.

        """

        if self._cancelled:
            raise CancelledError()

        if not self._done:
            self._wait = True
            
            self._sigint = pyev.Signal(signal.SIGINT, self.loop, lambda watcher, events: self._cancel(), None)
            self._sigint.start()

            if timeout and timeout > 0.0:
                self._timer = pyev.Timer(timeout, 0.0, self.loop,
                                         self._clear_wait, None)
                self._timer.start()

            while self._wait and not self._done and not self._cancelled:
                self.loop.start(pyev.EVRUN_ONCE)

        if self._cancelled:
            raise CancelledError()
        elif not self._done:
            raise TimeoutError()

    def _start_callbacks(self, result, exception):
        """Perform the callback chain going back and forth between the callback
        and errback as needed.

        If an exception is raised and the entire chain is gone through without a valid
        errback then its simply logged.

        """
        if self._cancelled:
            raise CancelledError()
        if self.called:
            raise AlreadyCalledError()

        self._result = result
        self._exception = exception
        if self._exception:
            self._tb_info = ''.join(traceback.format_tb(sys.exc_info()[2])) 
        self.called = True
        self._do_callbacks()

    def _do_callbacks(self):
        """Perform the callbacks."""
        self._done = False

        while self._callbacks and not self._cancelled:
            cb, eb, cb_args, cb_kwargs, eb_args, eb_kwargs = self._callbacks.pop()
            if cb and not self._exception:
                try:
                    self._result = cb(self._result, *cb_args, **cb_kwargs)
                    self._exception = False
                except Exception as e:
                    #logger.exception('deferred got exception while doing callback')
                    self._exception = True
                    self._result = e
                    self._tb_info = ''.join(traceback.format_tb(sys.exc_info()[2]))
            elif eb and self._exception:
                try:
                    self._result = eb(self._result, *eb_args, **eb_kwargs)
                    self._exception = False
                except Exception as e:
                    #logger.exception('deferred got exception while doing callback')
                    self._exception = True
                    self._result = e
                    self._tb_info = ''.join(traceback.format_tb(sys.exc_info()[2]))


        if self._exception:
            if Deferred.warnings:
                logger.warn('Unhandled Exception: ' + str(self._result))
            self._last_exception.exception = self._result
            self._last_exception.tb_info = self._tb_info
        else:
            self._last_exception.exception = None
            self._last_exception.tb_info = None

        self._done = True


class DeferredList(Deferred):
    def __init__(self, loop, cancelled_cb=None):
        Deferred.__init__(loop, cancelled_cb)
        self._deferreds = set()

    def add(self, deferred):
        self._deferreds.add(deferred)
        deferred.add_callback(self._markoff, deferred)

    def _markoff(self, deferred):
        self._deferreds.remove(deferred)
