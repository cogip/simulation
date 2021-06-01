# import time
from typing import Optional
from serial import Serial
from threading import Lock
# import ptvsd # Used to debug with VS Code

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot
from pydantic import parse_raw_as

from cogip import logger
from cogip import models
from cogip.entities.sensor import Sensor


class SerialController(QtCore.QObject):
    """
    This class controls the serial port used to communicate with the robot.
    Its main purpose is to get the shell menu to update the interface,
    get the robot position to update its position, and send the commands
    on the serial port.

    It runs in its own thread.

    Attributes:
        signal_new_console_text:
            Qt signal emitted to log messages in UI console
        signal_new_menu:
            Qt signal emitted to load a new menu
        signal_new_robot_state:
            Qt signal emitted on robot state update
        last_cycle:
            Record the last cycle to avoid sending the same data several times
    """
    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(models.ShellMenu)
    signal_new_robot_state: qtSignal = qtSignal(models.RobotState)
    last_cycle: int = 0

    def __init__(self, uart_device: str):
        """
        Class constructor.

        Arguments:
            uart_device: Serial port to open and control in this class.
        """

        super().__init__()

        # Set to true by the main thread to exit this thread after processing the current line
        self.exiting = False

        # Create the serial port, set its parameters, but do not open it yet
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 115200

        self.serial_lock = Lock()

        self.menu: Optional[models.ShellMenu] = None

    def quit(self):
        """
        Request to exit the thread as soon as possible.
        """
        self.exiting = True

    @qtSlot(str)
    def new_command(self, command: str):
        """
        Send a command to the robot.

        Arguments:
            command: Command to send
        """
        self.signal_new_console_text.emit(f"==> write '{command}'")
        logger.debug("new_cmd: try to acquire lock")
        with self.serial_lock:
            logger.debug("new_cmd: lock acquired")
            self.serial_port.write(command.encode()+b'\n')
        logger.debug("new_cmd: lock released")

    def process_output(self):
        """
        Main loop executed in a thread.

        Process the output of the serial port,
        parse the data and send corresponding information
        """
        # try:
        #     ptvsd.debug_this_thread()
        # except:
        #     pass

        # Open the serial port.
        # In simulation, it also starts the native firmware
        self.serial_port.open()

        self.new_command("_help_json")

        while not self.exiting:
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if len(line) == 0:
                continue
            try:
                message = parse_raw_as(models.SerialMessage, line)
                if isinstance(message, models.RobotState):
                    if message.cycle != self.last_cycle:
                        self.last_cycle = message.cycle
                        self.signal_new_robot_state.emit(message)
                elif isinstance(message, models.ShellMenu):
                    self.menu = message
                    self.signal_new_menu.emit(message)
                    for entry in self.menu.entries:
                        if entry.cmd == "_trace_on":
                            self.new_command("_trace_on")
                            entry.cmd = "_trace_off"
                        if entry.cmd == "_set_shmem_key" and Sensor.shm_key is None:
                            Sensor.init_shm()
                            self.new_command(f"_set_shmem_key {Sensor.shm_key}")
                elif isinstance(message, models.LogMessage):
                    self.signal_new_console_text.emit(message.log)
                    if message.log == "Press Enter to cancel planner start...":
                        self.new_command("")
                    elif message.log.startswith("Enter shell menu"):
                        self.new_command("_help_json")
            except:  # noqa
                self.signal_new_console_text.emit(line)

        if self.menu:
            for entry in self.menu.entries:
                if entry.cmd == "_trace_off":
                    self.new_command("_trace_off")

        self.serial_port.close()
