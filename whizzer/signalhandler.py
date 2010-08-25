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
import pyev

class SignalHandler(object):
    def __init__(self, loop):
        self.loop = loop
        self.sigint_watcher = pyev.Signal(signal.SIGINT, self.loop, self.handle_sigint)
        self.sigint_watcher.start()
        self.servers = []

    def register_server(self, server):
        """Registering a server with the signal handler will allow the server
        to be gracefully shutdown whenever a signal is caught. Otherwise
        its basically killed.
        """
        self.servers.append(server)

    def handle_sigint(self, watcher, events):
        """Catches the SIGINT signal and shutsdown all registered servers."""
        for server in self.servers:
            try:
                server.close()
            except Exception as e:
                print(e)
        self.loop.unloop()
