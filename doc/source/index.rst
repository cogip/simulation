Welcome to COGIP Simulator's documentation!
===========================================

Running the Simulator
=====================
.. argparse::
   :filename: ../bin/simulator.py
   :func: get_argument_parser
   :prog: simulator.py


Signals and Slots Connections
=============================

This diagram shows how the simulation classes are connected to each other using Qt Signals and Slots.
This is not an UML diagram.

THIS SCHEMA IS OUT-OF-DATE!

.. drawio:: qt_connections.drawio
    :alt: Qt Signals and Slots Connections
    :align: center


Modules Documentation
=====================

MainWindow Module
-----------------
.. automodule:: cogip.mainwindow
    :members:

Table Module
------------
.. automodule:: cogip.table
    :members:

Robot Module
------------
.. automodule:: cogip.robot
    :members:

SerialController Module
-----------------------
.. automodule:: cogip.serialcontroller
    :members:

Config Module
-------------
.. automodule:: cogip.config
    :members:


.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
