
import signal
import logging

import pyev

from .defer import Deferred, AlreadyCalledError, CancelledError, TimeoutError
from .protocol import Protocol, ProtocolFactory
from .server import SocketServer, TcpServer, UnixServer
from .client import SocketClient, TcpClient, UnixClient
from .transport import SocketTransport, ConnectionClosed

def _interrupt(self, watcher, events):
    watcher.loop.unloop()

def signal_handler(loop):
    """Install a basic signal handler watcher and return it."""
    watcher = pyev.Signal(signal.SIGINT, loop, _interrupt)
    return watcher



