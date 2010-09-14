========
Concepts
========

***********************
Socket Programming
***********************

Sockets are a way to stream bytes of data between programs, computers, even
outside of our very planet. However they have pitfalls that often times a
newcomer may miss. I know I certainly did.

Socket programming can be somewhat frustrating at times. For example
consider the two pieces of code below, about the simplest client and server
possible in python.

.. code-block:: python
   
    import socket

    mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mysock.connect(("10.10.10.10", 2000))
    mysock.send("Hello!")
    print("Sent Hello!")

.. code-block:: python

    import socket

    mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mysock.bind(("0.0.0.0", 2000))
    mysock.listen(1)

    (connection,address) = mysock.accept()
    print(connection.recv(6))


Depending on the kind of connection the mysock.send and connection.recv could
a long time to complete. This leaves both programs simply waiting around doing
nothing particularly useful.

**********************
Two Rivaling Solutions
**********************

There are two rivaling solutions to the problem of waiting for sockets and in
the more general sense input/output operations. Fork, threads, and select. All
of the solutions have their uses and using them together in some instances can
lead to greater performance. In the case of python the best solution is really
select. Python's GIL tends to scare most of us away from threads as a solution
to parallel execution.

**********************
Pyev
**********************

Whizzer is heavily based on pyev. Pyev acts as a loop with a set of event
watchers. When the event the watcher is looking for happens the callback
given to it when constructed is called. Pyev is very fast.

