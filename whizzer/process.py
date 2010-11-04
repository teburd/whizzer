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
import subprocess
import logbook
import pyev

logger = logbook.Logger(__name__)


class Process(object):
    """Acts as a wrapper around subprocess.Popen that provides logging and
    process watching using pyev instead of Popen.poll()

    """
    def __init__(self, loop, *args, **kwargs):
        """Setup a process object with the above arguments."""
        self.logger = logger
        self.loop = loop
        self.process = None
        self.args = args
        self.kwargs = kwargs
        self.watcher = None

    def start(self):
        """Start the process."""
        self.logger.info("starting process")
        self.process = subprocess.Popen(*self.args, **self.kwargs)
        self.watcher = pyev.Child(self.process.pid, False, self.loop, self._child)
        self.watcher.start()
    
    def stop(self):
        """Stop the process."""
        self.logger.info("stopping process")
        try:
            self.process.send_signal(signal.SIGTERM)
        except OSError as e:
            self.logger.warn("process already stopped")
            pass

    def _child(self, watcher, events):
        """Handle child watcher callback."""
        watcher.stop()
        self.crashed()

    def crashed(self):
        """Handle a process crash.
        
        This should be overridden if you wish to do 
        anything more than log that the process died.

        """
        self.logger.error("%s crashed" % self.args[0][0])


class ProcessGroup(object):
    """A container for a set of Process objects with some convienence
    methods to start and stop them all.
    
    """
    def __init__(self):
        """ProcessManager."""
        self.logger = logger
        self.processes = []

    def start(self):
        """Start all processes in the order they were added."""
        self.logger.info("starting all processes")
        for process in self.processes:
            process.start()

    def stop(self):
        """Stops all processes in the order they were added."""
        self.logger.info("stopping all processes")
        for process in self.processes:
            process.stop() 



