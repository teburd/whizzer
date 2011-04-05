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

import signal
import time
import os
import sys
import logbook
import pyev

logger = logbook.Logger(__name__)


class Process(object):
    """Acts as a wrapper around multiprocessing.Process/os.fork that provides logging
    and process watching using pyev.

    """
    def __init__(self, loop, run, *args, **kwargs):
        """Setup a process object with the above arguments."""
        self.loop = loop
        self.run = run
        self.args = args
        self.kwargs = kwargs
        self.watcher = None

    def start(self):
        """Start the process, essentially forks and calls target function.""" 
        logger.info("starting process")
        process = os.fork()
        time.sleep(0.01)
        if process != 0:
            logger.debug('starting child watcher')
            self.loop.reset()
            self.child_pid = process
            self.watcher = pyev.Child(self.child_pid, False, self.loop, self._child)
            self.watcher.start()
        else:
            self.loop.reset()
            logger.debug('running main function')
            self.run(*self.args, **self.kwargs) 
            logger.debug('quitting')
            sys.exit(0)

    def stop(self):
        """Stop the process."""
        logger.info("stopping process")
        self.watcher.stop()
        os.kill(self.child_pid, signal.SIGTERM)

    def _child(self, watcher, events):
        """Handle child watcher callback."""
        watcher.stop()
        self.crashed()

    def crashed(self):
        """Handle a process crash.
        
        This should be overridden if you wish to do 
        anything more than log that the process died.

        """
        self.logger.error("%s crashed" % self.child_pid)
