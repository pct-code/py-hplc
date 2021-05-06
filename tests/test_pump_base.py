"""This module tests the functionality of the NextGenPumpBase class."""

import sys
import unittest

from serial.serialutil import SerialException

from py_hplc.pump_base import NextGenPumpBase
from py_hplc.pump_error import PumpError


class TestPumpBase(unittest.TestCase):
    SERIAL_PORT = "COM3"  # this is machine-specific
    PUMP = None

    # setUp and tearDown will get run between each test method
    def setUp(self) -> None:
        try:
            self.PUMP = NextGenPumpBase(self.SERIAL_PORT)
        except SerialException:
            self.fail(f"No such port {self.SERIAL_PORT}")

    def tearDown(self) -> None:
        self.PUMP.close()

    def test_identify(self) -> None:
        """Tests initializing a NextGenPumpBase,
        as well as its .open and .identify methods.
        """
        self.assertTrue(self.PUMP.is_open)
        self.assertIsInstance(self.PUMP.max_flowrate, float)
        self.assertIsInstance(self.PUMP.max_pressure, (float, int))
        self.assertIsInstance(self.PUMP.version, str)
        self.assertIsInstance(self.PUMP.head, str)
        self.assertIsInstance(self.PUMP.flowrate_factor, int)

    def test_write_read(self) -> None:
        # redundant assertion that we can read/write
        self.assertIn("Version", self.PUMP.write("id"))

    def test_command(self) -> None:
        # make sure bad commands throw an error
        self.assertRaises(PumpError, self.PUMP.command, "foobar")

    def test_close(self) -> None:
        self.PUMP.close()
        self.assertFalse(self.PUMP.is_open)


if __name__ == "__main__":
    # pass in the serial port you want to test on
    # python -m unittest <FILE> <PORT>
    if len(sys.argv) > 1:
        TestPumpBase.SERIAL_PORT = sys.argv.pop()
    unittest.main()
