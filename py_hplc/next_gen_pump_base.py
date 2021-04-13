"""Serial port wrapper for Next Generation class pumps.
The code in this file establishes an OS-appropriate serial port and provides
an interface for communicating with the pumps.

"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from serial import SerialException, serial_for_url
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

from .pump_error import PumpError

if TYPE_CHECKING:
    from logging import Logger


COMMAND_END = b"\r"  # terminates messages sent
MESSAGE_END = b"/"  # terminates messages received


class NextGenPumpBase:
    """Serial port wrapper for MX-class Teledyne pumps."""

    def __init__(self, device: str, logger: Logger = None) -> None:
        # you'll have to reach in and add handlers yourself from the calling code
        if logger is None:  # append to the root logger
            self.logger = logging.getLogger(f"{logging.getLogger().name}.{device}")
        else:  # append to the passed logger
            self.logger = logging.getLogger(f"{logger.name}.{device}")

        # fetch a platform-appropriate serial interface
        self.serial = serial_for_url(
            device,
            baudrate=9600,
            bytesize=EIGHTBITS,
            do_not_open=True,
            parity=PARITY_NONE,
            stopbits=STOPBITS_ONE,
            timeout=0.1,  # 100 ms
        )

        # persistent identifying attributes
        self.max_flowrate: float = None
        self.max_pressure: float = None
        self.version: str = None
        self.pressure_units: str = None
        self.head: str = None
        # other -- for converting user args on the fly
        # 0.00 mL vs 0.000 mL; could rep. as 2 || 3?
        self.flowrate_factor: int = None  # used as 10 ** flowrate_factor

        # other configuration logic here
        self.open()  # open the serial connection
        self.identify()  # populate attributes, takes about 0.16 s on avg

    def open(self) -> None:
        """Open the serial port associated with the pump."""
        try:
            self.serial.open()
            self.logger.info("Serial port connected")
        except SerialException as err:
            self.logger.critical("Could not open a serial connection")
            self.logger.exception(err)

    def identify(self):
        """Get persistent pump properties."""
        # general properties -----------------------------------------------------------
        # firmware
        response = self.command("id")["response"]
        if "OK," in response:  # expect OK,<ID> Version <ver>/
            self.version = response.split(",")[1][:-1].strip()
        # pump head
        response = self.command("pi")["response"]
        if "OK," in response:
            self.head = response.split(',')[4]
        # max flowrate
        response = self.command("mf")["response"]
        if "OK,MF:" in response:  # expect OK,MF:<max_flow>/
            self.max_flowrate = float(response.split(":")[1][:-1])
        # volumetric resolution - used for setting flowrate
        # expect OK,<flow>,<UPL>,<LPL>,<p_units>,0,<R/S>,0/
        response = self.command("cs")["response"]
        precision = len(response.split(",")[1].split(".")[1])
        if precision == 2:  # eg. "5.00"
            self.flowrate_factor = -5  # FI takes microliters/min * 10 as ints
        elif precision == 3:  # eg. "5.000"
            self.flowrate_factor = -6  # FI takes microliters/min as ints

        # for pumps that have a pressure sensor ----------------------------------------
        # pressure units
        response = self.command("pu")["response"]
        if "OK," in response:  # expect "OK,<p_units>/"
            self.pressure_units = response.split(",")[1][:-1]
        # max pressure
        response = self.command("mp")["response"]
        if "OK,MP:" in response:  # expect "OK,MP:<max_pressure>/"
            self.max_pressure = float(response.split(":")[1][:-1])

    def command(self, command: str) -> dict[str, Any]:
        """Sends the passed string to the pump as bytes.

        Args:
            command (str): The message to be sent as bytes

        Raises:
            PumpError: An exception describing what went wrong

        Returns:
            dict[str, Any]: A dictionary containing at least a "response" key
            with the pump's response
        """
        response = self.write(command)
        if "Er/" in response:
            raise PumpError(
                command=command,
                response=response,
                message=f"The pump threw an error '{response}' in response to a command: '{command}'",
                port=self.serial.name,
            )

        return {"response": response}  # we parse this later and add entries

    def write(self, msg: str, delay: float = 0.015) -> str:
        """Write a command to the pump.

        A response will be returned after 2 * delay seconds.
        Delay defaults to 0.015 s per pump documentation.

        Returns the pump's response string.

        Args:
            msg (str): The message to be sent
            delay (float, optional): A float in seconds. Defaults to 0.015.

        Returns:
            str: the pump's decoded response string
        """
        response = ""
        tries = 0
        # pump docs recommend 3 attempts
        while tries < 3 and "OK" not in response:
            # this would clear the pump's command buffer, but shouldn't be relied upon
            # self.serial.write(b"#")
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            time.sleep(delay)  # could defer here if async
            # it seems getting pre-encoded strings from a dict is only slightly faster,
            # and only some of the time, when compared to just encoding args on the fly
            self.serial.write(msg.encode() + COMMAND_END)
            self.logger.debug("Sent %s (attempt %s/3)", msg, tries)
            # this sleeps on a tight loop until everything is written
            self.serial.flush()
            if msg == "#":  # this won't give a response
                break
            time.sleep(delay)  # could defer here if async
            response = self.read()
            tries += 1
        return response

    def read(self) -> str:
        """Reads a single message from the pump."""
        response = ""
        tries = 0
        while tries < 3 and "/" not in response:
            response = self.serial.read_until(MESSAGE_END).decode()
            self.logger.debug("Got response: %s", response)
            tries += 1
        return response

    def close(self) -> None:
        """Closes the serial port associated with the pump."""
        self.serial.close()
        self.logger.info("Serial port closed")

    @property
    def is_open(self) -> bool:
        """Returns a boolean representing if the internal serial port is open."""
        return self.serial.is_open
