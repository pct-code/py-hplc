"""This module tests the functionality of the NextGenPump class."""

import sys
import unittest
from time import sleep

from serial.serialutil import SerialException

from py_hplc.pump import (
    CurrentConditions,
    CurrentState,
    Faults,
    NextGenPump,
    PumpInfo,
    Solvents,
)
from py_hplc.pump_error import PumpError


class TestPump(unittest.TestCase):
    SERIAL_PORT = "COM3"
    PUMP = None

    # setUp and tearDown will get run between each test method
    def setUp(self) -> None:
        try:
            TestPump.PUMP = NextGenPump(self.SERIAL_PORT)
        except SerialException:
            self.fail(f"No such port {self.SERIAL_PORT}")

    def tearDown(self) -> None:
        self.PUMP.close()

    def test_run_stop(self) -> None:
        self.assertIn("OK", self.PUMP.run())
        sleep(3)  # give the pump a moment to stroke
        self.assertIn("OK", self.PUMP.stop())

    def test_keypad_disable_enable(self) -> None:
        self.assertIn("OK", self.PUMP.keypad_disable())
        self.assertIn("OK", self.PUMP.keypad_enable())

    def test_clear_faults(self) -> None:
        self.assertIn("OK", self.PUMP.clear_faults())

    def test_reset(self) -> None:
        # resets pump to factory defaults -- this could be distruptive
        # particularly if you care about your calibration / compensation values
        # self.assertIn('OK', self.PUMP.reset())

        pass

    def test_zero_seal(self) -> None:
        # this could be disruptive as the value cannot be set arbitrarily
        # the stroke counter can only be retreived or set to 0
        # self.assertIn('OK', self.PUMP.zero_seal())
        pass

    def test_current_conditions(self) -> None:
        conditions = self.PUMP.current_conditions()
        self.assertIsInstance(conditions, CurrentConditions)
        self.assertIsInstance(conditions.pressure, (float, int))
        self.assertIsInstance(conditions.flowrate, float)
        self.assertIsInstance(conditions.response, str)

    def test_current_state(self) -> None:
        state = self.PUMP.current_state()
        self.assertIsInstance(state, CurrentState)
        self.assertIsInstance(state.flowrate, float)
        self.assertIsInstance(state.upper_pressure_limit, (float, int))
        self.assertIsInstance(state.lower_pressure_limit, (float, int))
        self.assertIsInstance(state.pressure_units, str)
        self.assertIsInstance(state.response, str)

    def test_pump_information(self) -> None:
        info = self.PUMP.pump_information()
        self.assertIsInstance(info, PumpInfo)
        self.assertIsInstance(info.flowrate, float)
        self.assertIsInstance(info.is_running, bool)
        self.assertIsInstance(info.pressure_compensation, float)
        self.assertIsInstance(info.upper_pressure_fault, bool)
        self.assertIsInstance(info.lower_pressure_fault, bool)
        self.assertIsInstance(info.in_prime, bool)
        self.assertIsInstance(info.keypad_enabled, bool)
        self.assertIsInstance(info.motor_stall_fault, bool)
        self.assertIsInstance(info.response, str)

    def test_read_faults(self) -> None:
        faults = self.PUMP.read_faults()
        self.assertIsInstance(faults, Faults)
        self.assertIsInstance(faults.motor_stall_fault, bool)
        self.assertIsInstance(faults.upper_pressure_fault, bool)
        self.assertIsInstance(faults.lower_pressure_fault, bool)
        self.assertIsInstance(faults.response, str)

    def test_is_running(self) -> None:
        self.assertIsInstance(self.PUMP.is_running, bool)

    def test_stroke_counter(self) -> None:
        self.assertIsInstance(self.PUMP.stroke_counter, int)

    def test_flowrate_compensation(self) -> None:
        current = self.PUMP.flowrate_compensation
        self.assertIsInstance(current, float)
        self.PUMP.flowrate_compensation = current
        self.assertEqual(current, self.PUMP.flowrate_compensation)

    def test_flowrate(self) -> None:
        current = self.PUMP.flowrate
        self.assertIsInstance(current, float)
        self.PUMP.flowrate = current
        self.assertEqual(current, self.PUMP.flowrate)

    def test_pressure(self) -> None:
        self.assertIsInstance(self.PUMP.pressure, (float, int))

    def test_upper_pressure_limit(self) -> None:
        current = self.PUMP.upper_pressure_limit
        self.assertIsInstance(current, (float, int))
        self.PUMP.upper_pressure_limit = current
        self.assertEqual(current, self.PUMP.upper_pressure_limit)

    def test_lower_pressure_limit(self) -> None:
        current = self.PUMP.lower_pressure_limit
        self.assertIsInstance(current, (float, int))
        self.PUMP.lower_pressure_limit = current
        self.assertEqual(current, self.PUMP.lower_pressure_limit)

    def test_leak_detected(self) -> None:
        self.assertIsInstance(self.PUMP.leak_detected, bool)

    def test_set_leak_mode(self) -> None:
        # this value can only be set -- not retreived
        # self.assertIn('OK', self.PUMP.set_leak_mode(1))
        pass

    def test_solvent(self) -> None:
        # doesn't work with all models of pump
        try:
            self.PUMP.command("rs")
        except PumpError:
            return

        current = self.PUMP.solvent
        self.assertIsInstance(current, int)
        # also test passing in a solvent name
        self.PUMP.solvent = "water"
        self.assertEqual(self.PUMP.solvent, Solvents.WATER)
        self.PUMP.solvent = current
        self.assertEqual(current, self.PUMP.solvent)


if __name__ == "__main__":
    # pass in the serial port you want to test on
    # python -m unittest <FILE> <PORT>
    if len(sys.argv) > 1:
        TestPump.SERIAL_PORT = sys.argv.pop()
    unittest.main()
