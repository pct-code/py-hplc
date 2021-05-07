How to test the interface
=========================

Basic functionality can be tested for using Python's :code:`unittest` module.

- :code:`test_pump_base.py` contains tests for interacting with the serial connection
- :code:`test_pump.py` contains tests for the higher-level command wrappers 

The tests can be run as follows ::

    python -m unittest <PATH_TO_TEST> <PORT> 

- <PATH_TO_TEST> is the path to the test you want to run
- <PORT> is the local pump's serial port (eg. "COM3" or "/dev/ttyUSB0", etc.)

.. note::

    :code:`test_pump` will briefly run the pump, so make sure it is primed and connected to a solvent reservior.

.. note::

    Tests for :code:`NextGenPump`'s :code:`reset`, :code:`zero_seal`, and :code:`set_leak_mode` irreversibly modify the pump's configuration, and are disabled by default.