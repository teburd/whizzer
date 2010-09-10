
import signal
import logging

import pyev

from .futures import Future, Executor
from .protocol import Protocol, ProtocolFactory
from .server import SocketServer, TcpServer, UnixServer
from .client import SocketClient, TcpClient, UnixClient
from .transport import SocketTransport

class SignalHandler(object):
    """Simple signal handler."""
    def __init__(self, loop, logger=logging):
        self.loop = loop
        self.watcher = pyev.Signal(signal.SIGINT, loop, self._interrupt)
        self.watcher.start()

    def _interrupt(self, watcher, events):
        watcher.loop.unloop()
