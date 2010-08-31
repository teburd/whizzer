
import gc
import pyev

class ObjectWatcher(object):
    def __init__(self, loop, classes=[]):
        """Watches the garbage collector and prints out stats
        periodically with how many objects are in the gc for a given type.
        """
        self.classes = classes
        self.timer = pyev.Timer(1.0, 2.0, loop, self.print_stats)
        self.timer.start()

    def count(self, cls):
        return len([obj for obj in gc.get_objects() if isinstance(obj, cls)])

    def print_stats(self, watcher, events):
        print("Object Stats")
        for cls in self.classes:
            print("    %s : %d", % (cls.__name__, self.count(cls)))
