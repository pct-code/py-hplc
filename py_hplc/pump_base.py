"""Serial port wrapper for Next Generation class pumps.
The code in this file establishes an OS-appropriate serial port and provides
an interface for communicating with the pumps.

"""

from __future__ import annotations

import logging
from time import sleep
from typing import TYPE_CHECKING, Union

from serial import SerialException, serial_for_url
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE, SerialBase

from py_hplc.pump_error import PumpError

if TYPE_CHECKING:
    from logging import Logger


class NextGenPumpBase:
    """Serial port wrapper for MX-class Teledyne pumps."""

    def __init__(self, device: Union[SerialBase, str], logger: Logger = None) -> None:
        if isinstance(device, str):
            # fetch a platform-appropriate serial interface
            self.serial = serial_for_url(
                device,
                baudrate=9600,
                bytesize=EIGHTBITS,
                do_not_open=True,
                parity=PARITY_NONE,
                stopbits=STOPBITS_ONE,
                timeout=0.1,  # 100 ms
            )  # we have to manually open this later
        elif isinstance(device, SerialBase):
            self.serial = device
        else:
            raise ValueError("Must init using a Serial object or valid port string")

        # you'll have to reach in and add handlers yourself from the calling code
        if logger is None:  # append to the root logger
            self.logger = logging.getLogger(f"{logging.getLogger().name}.{device}")
        elif isinstance(logger, Logger):  # append to the passed logger
            self.logger = logging.getLogger(f"{logger.name}.{device}")

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
        if not self.is_open:
            self.open()  # open the serial connection
        self.identify()  # populate attributes, takes about 0.16 s on avg

    def open(self) -> None:
        """Opens the serial port associated with the pump.

        Raises: SerialException: An exception describing what went wrong. In this case,
        we failed to open the serial port.
        """
        try:
            self.serial.open()
            self.logger.info("Serial port connected")
        except SerialException as err:
            self.logger.critical("Could not open a serial connection")
            self.logger.exception(err)
            raise

    def identify(self) -> None:
        """Gets persistent pump properties."""
        # general properties -----------------------------------------------------------
        # pump head
        response = self.command("pi")
        if "OK," in response:
            self.head = response.split(",")[4]

        # max flowrate
        response = self.command("mf")
        if "OK,MF:" in response:  # expect OK,MF:<max_flow>/
            self.max_flowrate = float(response.split(":")[1][:-1])

        # volumetric resolution - used for setting flowrates later
        # expect OK,<flow>,<UPL>,<LPL>,<p_units>,0,<R/S>,0/
        response = self.command("cs")
        precision = len(response.split(",")[1].split(".")[1])
        if precision == 2:  # eg. "5.00"
            self.flowrate_factor = -5  # FI takes microliters/min * 10 as ints
        else:  # eg. "5.000"
            self.flowrate_factor = -6  # FI takes microliters/min as ints

        # version
        response = self.command("id")
        if "OK," in response:  # expect OK,<ID> Version <ver>/
            self.version = response.split(",")[1][:-1].strip()

        # for pumps that have a pressure sensor ----------------------------------------
        # pressure units
        response = self.command("pu")
        if "OK," in response:  # expect "OK,<p_units>/"
            self.pressure_units = response.split(",")[1][:-1]

        # max pressure
        response = self.command("mp")
        if "OK,MP:" in response:  # expect "OK,MP:<max_pressure>/"
            self.max_pressure = float(response.split(":")[1][:-1])

    def command(self, command: str) -> str:
        """Sends the passed string to the pump as bytes.

        Args:
            command (str): The message to be sent as bytes

        Raises:
            PumpError: An exception describing what went wrong. In this case, the pump
            reponded with an error code.

        Returns:
            dict[str, Any]: A dictionary containing at least a "response" key
            with the pump's response
        """
        response = self.write(command)
        if "Er/" in response:
            raise PumpError(
                command=command,
                response=response,
                message=(
                    f"The pump threw an error '{response}'"
                    f"in response to a command: '{command}'"
                ),
                port=self.serial.name,
            )

        return response  # we parse this later

    def write(self, msg: str, delay: float = 0.015) -> str:
        """Write a command to the pump.

        A response will be returned after at least (2 * delay) seconds.
        Delay defaults to 0.015 s per pump documentation.
        If we fail to get a "OK" response, we will wait 0.1 s before attempting again,
        up to 3 attempts.

        Returns the pump's response string.

        Raises:
            PumpError: An exception describing what went wrong. In this case, we
            couldn't get a response.

        Args:
            msg (str): The message to be sent
            delay (float, optional): A float in seconds. Defaults to 0.015.

        Returns:
            str: the pump's decoded response string
        """
        response = ""
        tries = 1
        cmd = "".join((msg, "\r")).encode()  # defaults to utf-8
        while tries <= 3:  # pump docs recommend 3 attempts
            # this would clear the pump's command buffer, but shouldn't be relied upon
            # self.serial.write(b"#")
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            sleep(delay)  # let the hardware buffers clear (could defer here if async)
            self.serial.write(cmd)
            self.serial.flush()  # sleeps on a tight loop until everything is written
            self.logger.debug("Sent %s (attempt %s/3)", msg, tries)

            if msg == "#":  # this won't give a response
                break
            sleep(delay)  # let the pump respond
            response = self.read()  # returns an already-decoded string
            if "OK" in response:  # no need to retry
                break
            tries += 1
            sleep(0.1)  # recommended delay between successive transmissions

        # let's throw an error if we couldn't get a response
        if response == "" and msg != "#":
            raise PumpError(
                command=msg,
                response=response,
                message=(f"Couldn't get a message from the pump in response to {msg}"),
                port=self.serial.name,
            )

        return response

    def read(self) -> str:
        """Reads a single message from the pump.

        Returns:
            str: The pump's response, or an empty string if no response is given.
        """
        response = b""
        tries = 1
        while tries <= 3:
            response = self.serial.read_until(b"/")  # we don't know the size a priori
            self.logger.debug("Got response: %s (attempt %s/3)", response, tries)
            if b"/" in response:  # b"/" is the pump's EOL flag
                break
            tries += 1

        return response.decode()

    def close(self) -> None:
        """Closes the serial port associated with the pump."""
        self.serial.close()
        self.logger.info("Serial port closed")

    @property
    def is_open(self) -> bool:
        """Returns a boolean representing if the internal serial port is open."""
        return self.serial.is_open
