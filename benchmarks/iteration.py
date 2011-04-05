import pyev
import time

def stop(watcher, events):
    watcher.loop.stop()


def timed(watcher, events):
    pass




loop = pyev.default_loop()
t1 = pyev.Timer(10.0, 0.0, loop, stop)
t2 = pyev.Timer(0.00000001, 0.00000001, loop, timed)
t1.start()
t2.start()

before = time.time()
loop.start()
after = time.time()

diff = after-before

ips = loop.iteration/diff

print("iterations per second: %f" % ips)
