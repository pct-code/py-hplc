"""Serial port wrapper for Next Generation pumps.
This module provides a thin Python wrapper around the pump's commands.
It uses properties to provide easy access to commonly used information about the pump.
It also handles the input/output parsing necessary to deal with
pumps using different pressure units or flowrate precisions.

When initializing the pump, you may pass in a reference to a logging.Logger instance as
the second argument.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING

from py_hplc.pump_base import NextGenPumpBase

if TYPE_CHECKING:
    from typing import Union


# these are more or less useful than an int
# LeakModes is currently unused
class LeakModes(Enum):
    LEAK_SENSOR_DISABLED = 0
    LEAK_DOES_NOT_FAULT = 1
    LEAK_DOES_FAULT = 2


# units are 10 ** -6 per bar
class Solvents(Enum):
    ACETONITRILE = 115
    HEXANE = 167
    ISOPROPANOL = 84
    METHANOL = 121
    TETRAHYDROFURAN = 54
    WATER = 46


# we return bundled data with these
@dataclass
class CurrentConditions:
    pressure: Union[float, int]
    flowrate: float
    response: str


@dataclass
class CurrentState:
    flowrate: float
    upper_pressure_limit: float
    lower_pressure_limit: float
    pressure_units: str
    is_running: bool
    response: str


@dataclass
class PumpInfo:
    flowrate: float
    is_running: bool
    pressure_compensation: float
    head: str
    upper_pressure_fault: bool
    lower_pressure_fault: bool
    in_prime: bool
    keypad_enabled: bool
    motor_stall_fault: bool
    response: str


@dataclass
class Faults:
    motor_stall_fault: bool
    upper_pressure_fault: bool
    lower_pressure_fault: bool
    response: str


class NextGenPump(NextGenPumpBase):
    """Serial port wrapper for Next Generation pumps.
    Commands to the pumps are available as methods on this object.

    Every command will return a dict representing the result of the command.
    This dict will contain at least a "response" key whose value is a string
    represtation of the pump's response.
    """

    def __init__(self, device: str, logger: Logger = None) -> None:
        """[summary]

        Args:
            device (str): [description]
            logger (Logger, optional): [description]. Defaults to None.
        """
        super().__init__(device, logger)

    # general pump commands ------------------------------------------------------------
    # these don't return anything besides a string saying 'OK/' if they succeed
    # if they didn't succeed, an exception would have been raised anyway -> return None
    def run(self) -> None:
        """Runs the pump."""
        self.command("ru")

    def stop(self) -> None:
        """Stops the pump."""
        self.command("st")

    def keypad_enable(self) -> None:
        """Enables the pump's keypad."""
        self.command("ke")

    def keypad_disable(self) -> None:
        """Disables the pump's keypad."""
        self.command("kd")

    def clear_faults(self) -> None:
        """Clears the pump's faults."""
        self.command("cf")

    def reset(self) -> None:
        """Resets the pump's user-adjustable values to factory defaults."""
        self.command("re")

    def zero_seal(self) -> None:
        """Zero the seal-life stroke counter."""
        self.command("zs")

    # bundled info retrieval -- these will return dataclasses --------------------------
    # all dicts have a "response" key whose value is the pump's decoded response string
    def current_conditions(self) -> CurrentConditions:
        """Returns a dataclass describing the current conditions of the pump.

        Returns:
            CurrentConditions: a dataclass with .pressure and .flowrate attributes
        """
        response = self.command("cc")
        msg = response.split(",")
        # OK,<pressure>,<flow>/
        if self.pressure_units == "psi":
            pressure = int(msg[1])
        else:
            pressure = float(msg[1])
        return CurrentConditions(
            pressure=pressure, flowrate=float(msg[2][:-1]), response=response
        )

    def current_state(self) -> CurrentState:
        """Returns a dataclass describing the current state of the pump.

        Returns:
            CurrentState: dataclass with .flowrate, .upper limit,
            .lower limit, .pressure units, .is running, and .response attributes
        """
        response = self.command("cs")
        # OK,<flow>,<UPL>,<LPL>,<p_units>,0,<R/S>,0/
        msg = response.split(",")
        return CurrentState(
            flowrate=float(msg[1]),
            upper_pressure_limit=float(msg[2]),
            lower_pressure_limit=float(msg[3]),
            pressure_units=msg[4],
            is_running=bool(int(msg[6])),
            response=response,
        )

    def pump_information(self) -> PumpInfo:
        """Gets a dictionary of information about the pump.

        Returns:
            PumpInfo: dataclass with .flowrate, .is_running,
            .pressure_compensation, .head, .upper_limit, .lower_limit, .in_prime,
            .keypad_enabled, .motor_stall_fault, and .response attributes
        """
        response = self.command("pi")
        # OK,<flow>,<R/S>,<p_comp>,<head>,0,1,0,0,<UPF>,<LPF>,<prime>,<keypad>,
        # 0,0,0,0,<stall>/
        msg = response.split(",")
        return PumpInfo(
            flowrate=float(msg[1]),
            is_running=bool(int(msg[2])),
            pressure_compensation=float(msg[3]),
            upper_pressure_fault=bool(int(msg[9])),
            lower_pressure_fault=bool(int(msg[10])),
            in_prime=bool(int(msg[11])),
            keypad_enabled=bool(int(msg[12])),
            motor_stall_fault=bool(int(msg[17][:-1])),
            response=response,
        )

    def read_faults(self) -> dict[str, bool]:
        """Returns a dictionary representing the pump's fault status.

        Returns:
            dict[str, bool]: "motor stall fault", "upper pressure fault",
            "lower pressure fault", "reponse"
        """
        response = self.command("rf")
        msg = response.split(",")
        # OK,<stall>,<UPF>,<LPF>/
        return Faults(
            motor_stall_fault=bool(int(msg[1])),
            upper_pressure_fault=bool(int(msg[2])),
            lower_pressure_fault=bool(int(msg[3][:-1])),
            response=response,
        )

    # general properties ---------------------------------------------------------------
    @property
    def is_running(self) -> None:
        """Returns a bool representing if the pump is running or not."""
        return self.current_state().is_running

    @property
    def stroke_counter(self) -> int:
        """Gets the seal-life stroke counter as an int."""
        response = self.command("gs")
        # OK,GS:<seal>/
        return int(response.split(":")[1][:-1])

    # flowrate compensation
    @property
    def flowrate_compensation(self) -> float:
        """Returns the flowrate compensation value as a float representing
        a percentage."""
        response = self.command("uc")
        # OK,UC:<user_comp>/
        return float(response.split(":")[1][:-1]) / 100

    @flowrate_compensation.setter
    def flowrate_compensation(self, value: float) -> None:
        """Sets the flowrate compensation to a factor between 0.85 and 1.15.
        Passing in a value out of bounds will default to the nearest bound.

        Args:
            value (float): The desired flowrate compensation,
            bounded between 0.85 and 1.15.
        """
        value = round(value, 2)
        if value < 0.85:
            value = 0.85
        elif value > 1.15:
            value = 1.15
        # pad leading 0s to 4 chars
        # eg. 0.85 -> 850 ->  UC0850
        # OK,UC:<user_comp>/
        self.command("uc" + f"{round(value * 1000):04}")

    @property
    def flowrate(self) -> float:
        """Gets/sets the flowrate of the pump as a float in mililiters per minute.

        Set values are bounded to the pump's max flowrate.

        Returns:
            float: the pump's flowrate in mililiters per minute
        """
        return self.current_conditions().flowrate

    @flowrate.setter
    def flowrate(self, flowrate: float) -> None:
        """Sets the flowrate of the pump to the passed value as a float representing
        mililiters per minute, not exceeding the pump's maximum.

        Args:
            flowrate (float): a float representing mililiters per minute
        """
        # convert arg as float mL to base units
        flowrate = flowrate / (10 ** 3)  # gets to L/min
        flowrate = round(flowrate / (10 ** self.flowrate_factor))
        self.command(f"fi{flowrate}")

    # individual properties for pressure enabled pumps ---------------------------------
    @property
    def pressure(self) -> Union[float, int]:
        """Gets the pump's current pressure as a float using the pump's pressure units.

        Pressure units are most easily found on a pump instance at .pressure_units
        """
        # beware using this on a tight loop https://stackoverflow.com/questions/6618002
        # OK,<pressure>/
        if self.pressure_units == "psi":
            return int(self.command("pr").split(",")[1][:-1])
        else:
            return float(self.command("pr").split(",")[1][:-1])

    # upper and lower pressure limits
    @property
    def upper_pressure_limit(self) -> float:
        """Gets/sets the pump's current upper pressure limit as a float.

        The units used can be inspected on the instance's pressure_units attribute.
        Values in bars can be precise to one digit after the decimal point.
        Values in MPa can be precise to two digits after the decimal point.
        """
        response = self.command("up")
        # OK,UP:<UPL>/
        return float(response.split(":")[1][:-1])

    @upper_pressure_limit.setter
    def upper_pressure_limit(self, limit: float) -> None:
        """Sets the upper pressure limit to a float in the pump's pressure units."""
        if self.pressure_units == "psi":
            limit = round(limit)
        elif self.pressure_units == "bar":
            limit = round(round(limit, 1) * 10)  # 19.99 -> 20.0 -> 200
        elif self.pressure_units == "MPa":
            limit = round(round(limit, 2) * 100)  # 1.999 -> 2.00 -> 200
        self.command(f"up{limit}")

    @property
    def lower_pressure_limit(self) -> float:
        """Gets/sets the lower pressurepump limit as a float.

        Units can be inspected on the instance's pressure_units attribute.
        Values in bars can be precise to one digit after the decimal point.
        Values in MPa can be precise to two digits after the decimal point.
        """
        response = self.command("lp")
        # OK,LP:<LPL>/
        return float(response.split(",")[1][:-1])

    @lower_pressure_limit.setter
    def lower_pressure_limit(self, limit: float) -> None:
        """Sets the pump's lower pressure limit."""
        if self.pressure_units == "psi":
            limit = round(limit)
        elif self.pressure_units == "bar":
            limit = round(round(limit, 1) * 10)  # 19.99 -> 20.0 -> 200
        elif self.pressure_units == "MPa":
            limit = round(round(limit, 2) * 100)  # 1.999 -> 2.00 -> 200
        self.command(f"lp{limit}")

    # properties for pumps with a leak sensor ------------------------------------------
    @property
    def leak_detected(self) -> bool:
        """Returns a bool representing if a leak is detected.
        Pumps without a leak sensor always return False.

        Returns:
            bool: [description]
        """
        response = self.command("ls")
        # OK,LS:<leak>/
        return bool(int(response.split(":")[1][:-1]))

    def set_leak_mode(self, mode: int) -> int:
        """Sets the pump's current leak mode as an int.

        0 if disabled. 1 if detected leak will fault. 2 if it will not fault.
        """
        # there seems to not be a way to query the current value without setting it
        if mode not in (0, 1, 2):
            raise ValueError(
                f"Invalid leak mode: {mode}. Choose from 0 (disabled), 1 (will fault), "
                "or 2 (won't fault)."
            )
        self.command(f"lm{mode}")  # OK,LM:<mode>/

    # properties for pumps with a solvent select feature ------------------------------
    # todo solvent select commands need testing
    @property
    def solvent(self) -> int:
        """Gets/sets the solvent compressibility value as an int in 10 ** -6 per bar.

        Alternatively, accepts the name of a solvent mapped in SOLVENT_COMPRESSIBILITY.
        See SOLVENT_COMPRESSIBILITY to get the solvent name.
        """
        # OK,<solvent>/
        return int(self.command("rs").split(",")[1][:-1])

    @solvent.setter
    def solvent(self, value: Union[str, int]) -> None:
        """Gets/sets the solvent compressibility value as an int in 10 ** -6 per bar."""
        # if we got a solvent name string, convert it to an int
        if value in Solvents.__members__:
            value = Solvents[value.upper()].value
        self.command(f"ss{value}")  # OK/
