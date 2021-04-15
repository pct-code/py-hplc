===========
py-hplc
===========

Overview
===========

This package wraps a serial connection with a thin Python interface to the commands available on SSI-Teledyne Next Generation HPLC pumps.

Some data about the pumps, such as pressure and flowrate, are exposed as Python properties.
This abstraction alleviates some of the inconsistencies involved in interfacing with various models of pump, and makes observing the pumps generally easier.

This is an unofficial wrapper. 

| View the `source`_.
| View the pump's official `user documentation`_.

.. _`source`: https://github.com/teauxfu/py-hplc
.. _`user documentation`: https://www.teledynessi.com/Manuals%20%20Guides/Product%20Guides%20and%20Resources/Serial%20Pump%20Control%20for%20Next%20Generation%20SSI%20Pumps.pdf

Requirements
=============
This package is 100% pure Python. Its only dependency is the fantastic `pySerial`_ library.

.. _`pySerial`: https://github.com/pyserial/pyserial

Installation
============
The package is available on PyPI ::

    pip install py-hplc

Using the package
==================
You can open a pump instance like this ::

   >>> from py_hplc import NextGenPump
   >>> pump = NextGenPump("COM3")  # or "/dev/ttyUSB0", etc.

You can inspect the pump for useful information such as its pressure units, firmware version, max flowrate, etc. ::

   >>> pump.version
   '191017 Version 2.0.8'
   >>> pump.pressure_units
   'psi'
   >>> pump.pressure
   100

The interface behaves in a typical way. Pumps can be inspected or configured without the use of getters and setters. ::

    >>> pump.flowrate
    10.0
    >>> pump.flowrate = 5.5  # mL / min
    >>> pump.flowrate
    5.5
    >>> pump.run()
    >>> pump.is_running
    True
    >>> pump.stop()
    >>> pump.is_running
    False
    >>> pump.leak_detected
    False

| Some pump commands, such as "CC" (current conditions), return many pieces of data at once.
| This package makes the data available in concise, descriptive, value-typed dictionaries. 

::

   >>> pump.current_conditions()
   {'response': 'OK,0000,10.00/', 'pressure': 0, 'flowrate': 10.0}
   >>> pump.read_faults()
   {'response': 'OK,0,0,0/', 'motor stall fault': False, 'upper pressure fault': False, 'lower pressure fault': False}

.. note::

    | Some pump commands return values of 0 or 1 that have no meaning.  
    | These are omitted from the dictionaries, but may be inspected using the "response" key. 
    
    ::

        >>> pump.pump_information()["response"]
        'OK,10.00,0,0,S10S,0,1,0,0,0,0,0,0,0,0,0,0,0/'



A somewhat lower-level interface is provided on the pump object's :code:`command` and :code:`write` methods. 
These methods are defined in :code:`NextGenPumpBase` and all pump methods rely on these internally. 
:code:`command` will always return a response dictionary, or raise an exception if the pump responds with an error code.
:code:`write` will only ever return the pump's decoded reponse as a string. ::

   >>> pump.command("pr")
   {'response': 'OK,0000/'}
   >>> pump.write("QQ")
   'OK, Debug Commands Enabled/'

.. note::

   | The :code:`write` command takes an optional :code:`delay` argument, which defaults to 0.015 s (15 ms). 
   | This delay is thread-blocking and occurs twice: once before the write operation and once before the read operation.
   | While these delays are not strictly necessary, they do make communication more robust. 
   |
   | If you need to take lots of pressure measurements very quickly, consider using :code:`write` instead of the :code:`pressure` property.

The connection to the serial port is opened automatically on initialization.
It can be manually closed when you're done with it. ::

   >>> pump.close()
   >>> pump.is_open
   False
   >>> pump.open()
   >>> pump.is_open
   True
