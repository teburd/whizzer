
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
    print("performing call")
    (d, method, args, kwargs) = watcher.data
    try:
        d.callback(method(*args, **kwargs))
    except Exception as e:
        d.errback(e)

def call_later(loop, logger, delay, method, *args, **kwargs):
    """Convienence method to create a timed function call."""
    d = Deferred(loop, logger=logger)
    t = pyev.Timer(delay, 0.0, loop, _perform_call, (d, method, args, kwargs))
    t.start()
    d.timer = t
    return d
