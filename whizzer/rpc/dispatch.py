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


class Dispatch(object):
    """Remote call dispatcher."""

    def __init__(self):
        """Instantiate a basic dispatcher."""
        self.functions = dict()

    def call(self, function, args=(), kwargs={}):
        """Call a method given some args and kwargs.

        function -- string containing the method name to call
        args -- arguments, either a list or tuple

        returns the result of the method.

        May raise an exception if the method isn't in the dict.

        """
        return self.functions[function](*args, **kwargs)

    def add(self, fn, name=None):
        """Add a function that the dispatcher will know about.

        fn -- a callable object
        name -- optional alias for the function

        """
        if not name:
            name = fn.__name__
        self.functions[name] = fn

def remote(fn, name=None, types=None):
    """Decorator that adds a remote attribute to a function.

    fn -- function being decorated
    name -- aliased name of the function, used for remote proxies
    types -- a argument type specifier, can be used to ensure
             arguments are of the correct type
    """
    if not name:
        name = fn.__name__

    fn.remote = {"name": name, "types": types}
    return fn


class ObjectDispatch(Dispatch):
    """Remote call dispatch 
    """
    def __init__(self, obj):
        """Instantiate a object dispatcher, takes an object
        with methods marked using the remote decorator

        obj -- Object with methods decorated by the remote decorator.

        """
        Dispatch.__init__(self)
        self.obj = obj
        attrs = dir(self.obj)
        for attr in attrs:
            a = getattr(self.obj, attr)
            if hasattr(a, 'remote'):
                self.add(a, a.remote['name'])


