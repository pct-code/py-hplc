========================================================================================
py-hplc |license| |python| |pypi| |build-status| |docs| |style| |code quality|
========================================================================================

Overview
==========
An unoffical Python wrapper for the SSI-Teledyne Next Generation class HPLC pumps.

- `Download page`_
- `API Documentation`_
- `Official pump documentation`_

MIT license, (C) 2021 Alex Whittington <alex@southsun.tech>

Installation
=============
The package is available on PyPI.

``python -m pip install --user py-hplc``


Using the package
==================

.. image:: https://raw.githubusercontent.com/teauxfu/py-hplc/main/docs/demo.gif
  :alt: gif demonstrating example usage

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

See the `API Documentation`_ for more usage examples.

.. _`Download page`: https://pypi.org/project/py-hplc/

.. _`API Documentation`: https://py-hplc.readthedocs.io/en/latest/

.. _`Official pump documentation`: https://www.teledynessi.com/Manuals%20%20Guides/Product%20Guides%20and%20Resources/Serial%20Pump%20Control%20for%20Next%20Generation%20SSI%20Pumps.pdf

.. |license| image:: https://img.shields.io/github/license/teauxfu/py-hplc
  :target: https://github.com/teauxfu/py-hplc/blob/main/LICENSE.txt
  :alt: GitHub

.. |python| image:: https://img.shields.io/pypi/pyversions/py-hplc
  :alt: PyPI - Python Version

.. |pypi| image:: https://img.shields.io/pypi/v/py-hplc
  :target: https://pypi.org/project/py-hplc/
  :alt: PyPI

.. |build-status| image:: https://github.com/teauxfu/py-hplc/actions/workflows/build.yml/badge.svg
  :target: https://github.com/teauxfu/py-hplc/actions/workflows/build.yml
  :alt: Build Status

.. |docs| image:: https://readthedocs.org/projects/pip/badge/?version=stable
  :target: https://py-hplc.readthedocs.io/en/latest/
  :alt: Documentation Status

.. |style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/psf/black
  :alt: Style

.. |code quality| image:: https://img.shields.io/badge/code%20quality-flake8-black
  :target: https://gitlab.com/pycqa/flake8
  :alt: Code quality
