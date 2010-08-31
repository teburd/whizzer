import signal
import pyev

from .server import UnixServer, TcpServer
from .client import UnixClient, TcpClient
from .protocol import Protocol, ProtocolFactory
from .futures import Future, Executor
from .errors import *

def stop_loop(watcher, events):
    watcher.loop.unloop()

def default_loop(*args):
    """Sets up a signal watcher and a pyev.default_loop."""
    loop = pyev.default_loop()
    loop.sigint_watcher = pyev.Signal(signal.SIGINT, loop, stop_loop)
    loop.sigint_watcher.start()
    loop.executor = Executor(loop)
    loop.call = loop.executor.submit
    loop.call_later = loop.executor.submit_delay
    return loop
