import time
from queue import Queue
from serial import Serial
from threading import Lock
# import ptvsd # Used to debug with VS Code

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot
from pydantic import ValidationError

from cogip import logger
from cogip.models import ShellMenu, PoseCurrent, DynObstacleList


class SerialController(QtCore.QObject):
    """SerialController class

    This class controls the serial port used to communicate with the robot.
    Its main purpose is to get the shell menu to update the interface,
    get the robot position to update its position, and send the commands
    on the serial port.

    It runs in its own thread.

    Extracted information is sent via Qt signals to
    :class:`~cogip.mainwindow.MainWindow` and :class:`~cogip.robot.Robot`
    """

    #: :obj:`qtSignal(str)`:
    #:      Qt signal emitted to log messages in UI console.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_new_console_text = qtSignal(str)

    #: :obj:`qtSignal(ShellMenu)`:
    #:      Qt signal emitted to load a new menu.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_new_menu = qtSignal(ShellMenu)

    #: :obj:`qtSignal(PoseCurrent)`:
    #:      Qt signal emitted to update Robot position.
    #:
    #:      Connected to :class:`~cogip.robotentity.RobotEntity`.
    signal_new_robot_position = qtSignal(PoseCurrent)

    #: :obj:`qtSignal(DynObstacleList)`:
    #:      Qt signal emitted to update dynamic obstacles.
    #:
    #:      Connected to :class:`~cogip.robotentity.RobotEntity`.
    signal_new_dyn_obstacles = qtSignal(DynObstacleList)

    max_parse_attemps = 20

    def __init__(self, uart_device: str, position_queue: Queue):
        """:class:`SerialController` constructor.

        Args:
            uart_device (str): Serial port to open and control in this class.
            position_queue (Queue):
                Queue containing robot position,
                filled by :class:`~cogip.serialcontroller.SerialController`
        """

        QtCore.QObject.__init__(self)
        self.position_queue = position_queue

        # Record last position to send a position only once
        self.last_position = (-1, -1, -1)

        # Set to true by the main thread to exit this thread after processing the current line
        self.exiting = False

        # Create the serial port, set its parameters, but do not open it yet
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 115200

        self.menu_has_pose = False
        self.serial_lock = Lock()

    def quit(self):
        """Request to exit the thread as soon as possible.
        """
        self.exiting = True

    @qtSlot(str)
    def slot_new_command(self, command: str):
        self.signal_new_console_text.emit(f"==> write '{command}'")
        logger.debug("new_cmd: try to acquire lock")
        with self.serial_lock:
            logger.debug("new_cmd: lock acquired")
            self.serial_port.write(command.encode()+b'\n')
        logger.debug("new_cmd: lock released")
        self.reload_menu()

    def reload_menu(self):
        self.menu_has_pose = False

        logger.debug("reload_menu: try to acquire lock")
        with self.serial_lock:
            logger.debug("reload_menu: lock acquired")
            self.serial_port.write(b"_help_json\n")

            while True:
                line = self.serial_port.readline().rstrip().decode(errors="ignore")
                if line[0] == ">":
                    continue
                try:
                    menu = ShellMenu.parse_raw(line)
                    self.signal_new_menu.emit(menu)
                    for entry in menu.entries:
                        if entry.cmd == "_pose":
                            self.menu_has_pose = True
                            break
                    break
                except ValidationError:
                    self.signal_new_console_text.emit(line)
        logger.debug("reload_menu: lock released")

    def process_output(self):
        """Main loop executed in a thread.
        Process the output of the serial port, parse the data and send corresponding information
        """
        # try:
        #     ptvsd.debug_this_thread()
        # except:
        #     pass

        # Open the serial port.
        # In simulation, it also starts the native firmware
        self.serial_port.open()

        # Initialization loop
        logger.debug("Waiting for calibration mode")
        exit_loop = False
        while not self.exiting and not exit_loop:
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if line == "Press Enter to enter calibration mode...":
                exit_loop = True
            self.signal_new_console_text.emit(line)

        self.serial_port.write(b"\n")

        self.reload_menu()

        while not self.exiting:
            time.sleep(0.01)
            if not self.menu_has_pose:
                continue
            logger.debug("main_loop: try to acquire lock")
            with self.serial_lock:
                logger.debug("main_loop: lock acquired")

                self.get_pose()

                self.get_dyn_obstacles()

            logger.debug("main_loop: lock released")

        # Close the serial port before exiting the thread
        self.serial_port.close()

    def get_pose(self):
        self.serial_port.write(b"_pose\n")

        pose_found = False
        attempt = 0
        while (not self.exiting and not pose_found
                and attempt < SerialController.max_parse_attemps):
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if line[0] == ">":
                continue
            try:
                pose = PoseCurrent.parse_raw(line)
                self.signal_new_robot_position.emit(pose)
                pose_found = True
            except ValidationError:
                attempt += 1
                self.signal_new_console_text.emit(line)
                # print(f"parse failed: {line}")

    def get_dyn_obstacles(self):
        self.serial_port.write(b"_dyn_obstacles\n")

        obstacles_found = False
        attempt = 0
        while (not self.exiting and not obstacles_found
                and attempt < SerialController.max_parse_attemps):
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if line[0] == ">":
                continue
            try:
                dyn_obstacles = DynObstacleList.parse_raw(line)
                self.signal_new_dyn_obstacles.emit(dyn_obstacles)
                obstacles_found = True
                # print(dyn_obstacles)
            except ValidationError:
                attempt += 1
                self.signal_new_console_text.emit(line)
                # print(f"parse failed: {line}")
