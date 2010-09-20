
import signal
import logging

import pyev

from .defer import Deferred, AlreadyCalledError, CancelledError, TimeoutError
from .protocol import Protocol, ProtocolFactory
from .server import SocketServer, TcpServer, UnixServer
from .client import SocketClient, TcpClient, UnixClient
from .transport import SocketTransport, ConnectionClosed

def _interrupt(watcher, events):
    watcher.loop.unloop()

def signal_handler(loop):
    """Install a basic signal handler watcher and return it."""
    watcher = pyev.Signal(signal.SIGINT, loop, _interrupt)
    return watcher

def _perform_call(watcher, events):
    (method, args, kwargs) = watcher.data

def call_later(loop, delay, method, *args, **kwargs):
    """Convienence method to create a timed function call."""
    t = pyev.Timer(delay, 0.0, loop, _perform_call, (method, args, kwargs))
    t.start()
    return t
