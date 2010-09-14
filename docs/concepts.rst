========
Concepts
========

***********************
Socket Programming
***********************

When I first learned about sockets I thought they were magical.

Here was a way I could have two programs across the world communicate with 
eachother with relatively little effort. Especially with python!

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
    connection.close()

Sockets are not magical, they can however be difficult to wrangle them to do
what you want when you want them.

The real problem however that most people have with sockets that event loops
and asynchronous programming attempts to solve is waiting for them!

Depending on the kind of connection the mysock.send call could take up to
hours to complete on the above tcp socket connection example. Really!

********************************
What it means to be Event Driven
********************************

Event driven programs are simple in concept. Upon some event occuring such as
a mouse click or key press some part of the program registered with that event
is run. The events most people care about when programming with sockets are
readable, writtable, and time out events.

********************************
What is means to be Asynchronous
********************************

Asynchronous programs use events to avoid waiting. By avoiding waiting an 
asynchronous program can do more work in less time. In the above blocking
socket example the call mysock.send() may take hours to complete however
unlikely. To avoid waiting for the send call to complete, which when using
a TCP socket means the data really has been sent to the client, we instead
simply send it and assume the data is actually sent by the operating system.

.. code-block:: python

   import socket
   import select
   mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   mysock.connect(("10.10.10.10", 2000))
   mysock.set_blocking(False)
   mysock.send("Hello!")
   print("Sent Hello!")

Suddenly send will no longer block the program until the data has been sent,
instead the operating system will buffer everything and send it as quickly
as it can.

But wait a second, there is now a buffer. What happens when the program sends
data too quickly?

.. code-block:: python

   import socket
   import select
   mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   mysock.connect(("10.10.10.10", 2000))
   mysock.set_blocking(False)
   while True:
       mysock.send("Hello!")

Hello IOError! mysock.send will result in an exception very quickly.

This is where event driven programming comes in to play!

Notably an asynchronous program does not automatically gain more computational power
it simply makes better use of time.
