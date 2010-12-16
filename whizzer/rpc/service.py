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

import logbook

from whizzer.process import Process
from whizzer.rpc.dispatch import remote

logger = logbook.Logger(__name__)


def spawn_link(service, *args, **kwargs):
    """Spawn a linked process such that when that process dies
    the current one will also die. This happens by signaling the current
    process with SIGINT. This returns a Proxy to the spawned service.

    """

def spawn_notify(notify, service, *args, **kwargs):
    """Spawn a process such that when that process dies the given callback
    is called with the Process object.

    """

def ServiceProxy(object):
    """Proxy to a service, easily serialized and reconstructed."""

class Service(object)
    """A generic service class meant to be run in a process on its own and
    handle requests using RPC.

    """

    def __init__(self, name):
        """Create a service with a name."""

    @remote
    def call(self, caller, name, *args, **kwargs):
        """Handle a remote call."""

    @remote
    def cast(self, name, *args, **kwargs):
        """Handle a remote notification."""

    @remote
    def stop(self, reason):
        """Shutdown the service with a reason."""


    def terminate(self, reason):
        """
