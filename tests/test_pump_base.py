import sys
import unittest

from serial.serialutil import SerialException

from py_hplc.pump_base import NextGenPumpBase
from py_hplc.pump_error import PumpError


class TestPumpBase(unittest.TestCase):
    SERIAL_PORT = "COM3"
    PUMP = None

    def setUp(self) -> None:
        # will both .open() and .identify() on init
        try:
            TestPumpBase.PUMP = NextGenPumpBase(self.SERIAL_PORT)
        except SerialException:
            self.fail(f"No such port {self.SERIAL_PORT}")

    def test_identify(self) -> None:
        """Tests initializing a NextGenPumpBase,
        as well as its .open and .identify methods.
        """
        pump = TestPumpBase.PUMP
        self.assertTrue(pump.is_open)
        self.assertIsNotNone(pump.max_flowrate)
        self.assertIsNotNone(pump.max_pressure)
        self.assertIsNotNone(pump.version)
        self.assertIsNotNone(pump.head)
        self.assertIsNotNone(pump.flowrate_factor)

    def test_write_read(self) -> None:
        pump = TestPumpBase.PUMP
        # redundant assertion that we can read/write
        self.assertIn("Version", pump.write("id"))

    def test_command(self) -> None:
        # make sure bad commands throw an error
        pump = TestPumpBase.PUMP
        self.assertRaises(PumpError, pump.command, "foobar")

    def test_close(self) -> None:
        pump = TestPumpBase.PUMP
        pump.close()
        self.assertFalse(pump.is_open)


if __name__ == "__main__":
    # pass in the serial port you want to test on
    if len(sys.argv) > 1:
        TestPumpBase.SERIAL_PORT = sys.argv.pop()
    unittest.main()
