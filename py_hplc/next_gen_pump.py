"""Serial port wrapper for Next Generation pumps.
This module provides a thin Python wrapper around the pump's commands.
It uses properties to provide easy access to commonly used information about the pump.
It also handles the input/output parsing necessary to deal with
pumps using different pressure units or flowrate precisions.
"""

from __future__ import annotations

from logging import Logger
from typing import TYPE_CHECKING

from .next_gen_pump_base import NextGenPumpBase

if TYPE_CHECKING:
    from typing import Union


# these are more or less useful than an int
# currently unused
LEAK_MODES = {
    0: "leak sensor disabled",
    1: "detected leak does not cause fault",
    2: "detected leak does cause fault",
}
# units are 10 ** -6 per bar
SOLVENT_COMPRESSIBILITY = {
    "acetonitrile": 115,
    "hexane": 167,
    "isopropanol": 84,
    "methanol": 121,
    "tetrahydrofuran": 54,
    "water": 46,
}

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
        NextGenPumpBase.__init__(self, device, logger)

    # general pump commands ------------------------------------------------------------

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
        """Zero the seal-life stroke counter. 0"""
        self.command("zs")

    # bundled info retrieval -- these will return dicts -------------------------------
    # all dicts have a "response" key whose value is the pump's decoded response string
    def current_conditions(self) -> dict[str, Union[float, str]]:
        """Returns a dictionary describing the current conditions of the pump.

        Returns:
            dict[str, Union[float, int, str]]: keys "pressure", "flowrate", "response"
        """
        result = self.command("cc")
        msg = result["response"].split(",")
        # OK,<pressure>,<flow>/
        if self.pressure_units == "psi":
            result["pressure"] = int(msg[1])
        else:
            result["pressure"] = float(msg[1])
        result["flowrate"] = float(msg[2][:-1])
        return result

    def current_state(self) -> dict[str, Union[bool, float, int, str]]:
        """Returns a dictionary describing the current state of the pump.

        Returns:
            dict[str, Union[bool, float, str]]: keys "flowrate", "upper limit",
            "lower limit", "pressure units", "is running", "response"
        """
        result = self.command("cs")
        # OK,<flow>,<UPL>,<LPL>,<p_units>,0,<R/S>,0/
        msg = result["response"].split(",")
        result["flowrate"] = float(msg[1])
        result["upper limit"] = float(msg[2])
        result["lower limit"] = float(msg[3])
        result["pressure units"] = msg[4]
        result["is running"] = bool(int(msg[6]))
        return result

    def pump_information(self) -> dict[str, Union[float, int, str]]:
        """Gets a dictionary of information about the pump.

        Returns:
            dict[str, Union[bool, float, str]]: "flowrate", "is running",
            "pressure compensation", "head", "upper limit", "lower limit", "in prime",
            "keypad enabled", "motor stall fault", "response"
        """
        result = self.command("pi")
        # OK,<flow>,<R/S>,<p_comp>,<head>,0,1,0,0,<UPF>,<LPF>,<prime>,<keypad>,
        # 0,0,0,0,<stall>/
        msg = result["response"].split(",")
        result["flowrate"] = float(msg[1])
        result["is running"] = bool(int(msg[2]))
        result["pressure compensation"] = float(msg[3])
        result["head"] = msg[4]
        result["upper limit fault"] = bool(int(msg[9]))
        result["lower limit fault"] = bool(int(msg[10]))
        result["in prime"] = bool(int(msg[11]))
        result["keypad enabled"] = bool(int(msg[12]))
        result["motor stall fault"] = bool(int(msg[17][:-1]))
        return result

    def read_faults(self) -> dict[str, bool]:
        """Returns a dictionary representing the pump's fault status.

        Returns:
            dict[str, bool]: "motor stall fault", "upper pressure fault",
            "lower pressure fault", "reponse"
        """
        result = self.command("rf")
        msg = result["response"].split(",")
        # OK,<stall>,<UPF>,<LPF>/
        result["motor stall fault"] = bool(int(msg[1]))
        result["upper pressure fault"] = bool(int(msg[2]))
        result["lower pressure fault"] = bool(int(msg[3][:-1]))
        return result

    # general properties  ---------------------------------------------
    @property
    def is_running(self) -> None:
        """Returns a bool representing if the pump is running or not."""
        return self.current_state()["is running"]

    @property
    def stroke_counter(self) -> int:
        """Gets the seal-life stroke counter as an int."""
        result = self.command("gs")
        # OK,GS:<seal>/
        return int(result["response"].split(":")[1][:-1])

    # flowrate compensation
    @property
    def flowrate_compensation(self) -> float:
        """Returns the flowrate compensation value as a float representing a percentage."""
        result = self.command("uc")
        # OK,UC:<user_comp>/
        return float(result["response"].split(":")[1][:-1]) / 100

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
        return self.current_conditions()["flowrate"]

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
        # OK,<pressure>/
        if self.pressure_units == "psi":
            return int(self.command("pr")["response"].split(",")[1][:-1])
        else:
            return float(self.command("pr")["response"].split(",")[1][:-1])


    # upper and lower pressure limits
    @property
    def upper_pressure_limit(self) -> float:
        """Gets/sets the pump's current upper pressure limit as a float.

        The units used can be inspected on the instance's pressure_units attribute.
        Values in bars can be precise to one digit after the decimal point.
        Values in MPa can be precise to two digits after the decimal point.
        """
        result = self.command("up")
        # OK,UP:<UPL>/
        return float(result["response"].split(":")[1][:-1])

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
        result = self.command("lp")
        # OK,LP:<LPL>/
        return float(result["response"].split(",")[1][:-1])

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
        result = self.command("ls")
        # OK,LS:<leak>/
        return bool(int(result["response"].split(":")[1][:-1]))

    @property
    def leak_mode(self) -> int:
        """Gets/sets the pump's current leak mode as an int.
        See LEAK_MODES for a map.

        Returns:
            int: 0 if disabled. 1 if detected leak will fault. 2 if it will not fault.
        """
        result = self.command("lm")
        # OK,LM:<mode>/
        return int(result["response"].split(":")[1][:-1])
        # could return a descriptive string instead
        # return LEAK_MODES.get(int(result["response"].split(":")[1][:-1]))
        

    @leak_mode.setter
    def leak_mode(self, mode: int) -> None:
        """Sets the pump's leak mode."""
        # todo test how pump responds to out of bounds
        self.command(f"lm{mode}")

    # properties for pumps with a solvent select feature ------------------------------
    @property
    def solvent(self) -> int:
        """Gets/sets the solvent compressibility value in 10 ** -6 per bar.

        Alternatively, accepts the name of a solvent mapped in SOLVENT_COMPRESSIBILITY.
        See SOLVENT_COMPRESSIBILITY to get the solvent name.
        """
        # OK,<solvent>/
        return int(self.command("rs")["response"].split(",")[1][:-1])

    @solvent.setter
    def solvent(self, value: Union[str, int]) -> None:
        """Gets/sets the solvent compressibility value in 10 ** -6 per bar."""
        # if we got a solvent name string, convert it to an int
        if value in SOLVENT_COMPRESSIBILITY.keys():
            value = SOLVENT_COMPRESSIBILITY.get(value)
        self.command(f"ss{value}")  # OK/
