Welcome to py-mx-hplc's documentation!

The goal of py-mx-hplc is to provide a class which encapsulates a serial connection and the commands available on SSI-Teledyne Next Generation HPLC pumps.
Some information about the pump, such as pressure and flowrate, have been abstracted as Python properties available on instances of the class.
This abstraction alleviates some of the inconsistencies involved in interfacing with various models of pump, and makes observing the pumps generally easier.

This is an unofficial, non-endorsed wrapper. 

View the source_.
.. _source: https://github.com/teauxfu/py-mx-hplc


======================================
.. toctree::
   :caption: Contents:

   pump
   pump_base


Using the package
------------------
First, install the package::

   python -m pip install --user py-mx-hplc

You can open a pump instance like this::

   >>> from py-mx-hplc import NextGenPump
   >>> pump = NextGenPump("COM3")  # or "/dev/ttyUSB0", etc.

You can inspect the pump for useful information such as its pressure units, firmware version, max flowrate, etc. ::

   >>> pump.pressure_units
   'psi'

Many pump commands, such as "CC" or "PI", return many pieces of data at once and occasionally include some noise.
This package makes this data available in descriptive dictionaries. ::

   >>> pump.current_conditions()
   {'pressure': 1000, 'flowrate': 10.0, 'response': 'OK,0522,12.00'}

The dictionary values are already cast to an appropriate type (string, float, bool).
The pump's actual response is always mapped to the 'reponse' key, so it's easy to parse it yourself if the need arises.

   >>> pump.flowrate = 5.5  # mL / min
   >>> pump.run()
   >>> pump.is_running
   True
   >>> pump.stop()
   >>> pump.is_running
   False

The connection to the serial port is opened automatically on initialization.
It must be manually closed when you're done with it. ::

   >>> pump.is_open
   True
   >>> pump.close()
   >>> pump.is_open
   False
   >>> pump.open()
   >>> pump.is_open
   True



Indices and search
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
