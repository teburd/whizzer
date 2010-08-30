
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

import pyev
import sys
import signal

class CancelledError(Exception):
    """CancelledError describes an error state for a future object."""

class TimeoutError(Exception):
    """TimeoutError describes an error state for a future object."""

class PerformedError(Exception):
    """PerformedError describes an error state for a future object."""

class RuntimeError(Exception):
    """PerformedError describes an error state for a future object."""

class Executor(object):
    def __init__(self, loop):
        self._loop = loop
        self._watchers = set()

    def submit(self, fn, *args, **kwargs):
        """Submit a function to be executed sometime in the future.

        Returns a Future object.

        """
        return self._submit(0.0, 0.0, fn, args, kwargs)
        
    def submit_delay(self, delay, fn, *args, **kwargs):
        """Perform a call in the future with a given delay in seconds.

        Returns a Future object

        """
        return self._submit(delay, 0.0, fn, args, kwargs)

    def _submit(self, delay, repeat_delay, fn, args, kwargs):
        future = Future(self._loop)
        watcher = pyev.Timer(delay, repeat_delay, self._loop, self._perform, (future, fn, args, kwargs))
        watcher.start()
        self._watchers.add(watcher)
        return future

    def _perform(self, watcher, events):
        try:
            (future, fn, args, kwargs) = watcher.data
            if future.done():
                self._watchers.remove(watcher)
                return

            if not future.set_running_or_notify_cancel():
                self._watchers.remove(watcher)
                return
            try:
                future.set_result(fn(*args, **kwargs))
            except Exception as e:
                future.set_exception(e)
            if watcher.repeat == 0.0:
                self._watchers.remove(watcher)
        except Exception as e:
            sys.stderr.write(str(e))

    def map(self, fn, timeout=None, *iterables):
        """Apply a function to each element in an iterable.

        Applies a function to each element in an iterable over time.

        Timeout will force the map to result in an TimeoutError if it
        exceeds the given value.

        Returns a Future object.

        """

    def shutdown(self, wait=True):
        """Shutdown the executor, if wait=True then the call will block until all
        submitted calls are completed.

        submit_repeating calls will be stopped automatically when shutdown is
        called.

        """


class Future(object):
    """Future represents a future result. This is the return of an asynchronous
    call as the result is not known yet!
    
    Taken from the PEP3148, part of python 3.2 but not part of python 2.6 or
    python 3.1.

    """
    def __init__(self, loop):
        self._loop = loop
        self._cancelled = False
        self._cancelled_callbacks = []
        self._running = False
        self._done = False
        self._done_callbacks = []
        self._result = None
        self._exception = None
        self._wait = False
        self._timer = None
        self.sigint_watcher = pyev.Signal(signal.SIGINT, self._loop, self._interrupt)
        self.sigint_watcher.start()

    def _interrupt(self, watcher, events):
        """A signal may be caught while waiting for something, if so, its assumed the future is cancelled."""
        if not self._done and self._wait:
            self._cancelled = True
            self._wait = False
        else:
            self.cancel()
        
    def cancel(self):
        """Cancel the future results.
        
        Attempt to cancel the call. If the call is currently being executed 
        then it cannot be cancelled and the method will return False, 
        otherwise the call will be cancelled and the method will return True.

        """
        if self._running == True:
            return False
        else:
            self._cancelled = True
            self._perform_callbacks()
            return True

    def cancelled(self):
        """Return True if the call was successfully cancelled."""
        return self._cancelled

    def running(self):
        """Return True if the call is currently being executed and cannot be cancelled."""
        return self._running

    def done(self):
        """Return True if the call was successfully cancelled or finished running."""
        return (self._cancelled or self._done)

    def add_done_callback(self, fn):
        """Attaches a callable fn to the future that will be called when the
        future is cancelled or finishes running. fn will be called with the
        future as its only argument.

        Added callables are called in the order that they were added and are
        always called in a thread belonging to the process that added them. If
        the callable raises an Exception then it will be logged and ignored. If
        the callable raises another BaseException then behavior is not defined.

        If the future has already completed or been cancelled then fn will be
        called immediately.
        """
        self._done_callbacks.append(fn)

    def set_running_or_notify_cancel(self):
        """Should be called by Executor implementations before executing the
        work associated with the Future.

        If the method returns False then the Future was cancelled, i.e.
        Future.cancel was called and returned True. Any threads waiting on the
        Future completing (i.e. through as_completed() or wait()) will be woken
        up.

        If the method returns True then the Future was not cancelled and has
        been put in the running state, i.e. calls to Future.running() will
        return True.

        This method can only be called once and cannot be called after
        Future.set_result() or Future.set_exception() have been called.
        
        """
        assert(not self._running and not self._done)

        if self._cancelled:
            return False
        else:
            self._running = True
            return True

    def set_result(self, result):
        """Sets the result of the work associated with the Future."""
        self._result = result
        self.set_done()

    def set_exception(self, exception):
        """Sets the result of the work associated with the Future to the given
        Exception.
        
        """
        self._exception = exception
        self.set_done()

    def set_done(self):
        """Sets the status of the future as being completed."""
        self._done = True
        self._running = False
        self._perform_callbacks()

    def _perform_callbacks(self):
        for callback in self._done_callbacks:
            callback(self)
   
    def _clear_wait(self, watcher, events):
        self._wait = False

    def _do_wait(self, timeout):
        """Wait for the future to be completed for a period of time

        Raises TimeoutError if the wait times out before the future is done.
        Raises CancelledError if the future is cancelled before the
        timeout is done.
        
        """

        if self._cancelled:
            raise CancelledError()

        if not self._done: 
            self._wait = True
    
            if timeout and timeout > 0.0: 
                self._timer = pyev.Timer(timeout, 0.0, self._loop, self._clear_wait, None)
                self._timer.start()

            while self._wait and not self._done and not self._cancelled:
                self._loop.loop(pyev.EVLOOP_ONESHOT)
          
        if self._cancelled:
            raise CancelledError()
        elif not self._done:
            raise TimeoutError()

    def result(self, timeout=None):
        """Return the value returned by the call. 
        
        If the call hasn't yet completed then this method will wait up to
        timeout seconds. If the call hasn't completed in timeout seconds then a
        TimeoutError will be raised. If timeout is not specified or None then
        there is no limit to the wait time.

        If the future is cancelled before completing then CancelledError will
        be raised.

        If the call raised then this method will raise the same exception.

        """
        self._do_wait(timeout)

        if self._exception:
            raise self._exception
        else:
            return self._result

    
    def exception(self, timeout=None):
        """Return the exception raised by the call. 
        
        If the call hasn't yet completed then this method will wait up to
        timeout seconds. If the call hasn't completed in timeout seconds then a
        TimeoutError will be raised. If timeout is not specified or None then
        there is no limit to the wait time.

        If the future is cancelled before completing then CancelledError will
        be raised.

        If the call completed without raising then None is returned.
        
        """
        self._do_wait(timeout)

        return self._exception


