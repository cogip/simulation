import time
from queue import Queue
from serial import Serial
from threading import Lock
# import ptvsd # Used to debug with VS Code

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal as qtSignal
from PyQt5.QtCore import pyqtSlot as qtSlot
from pydantic import ValidationError

from cogip import logger
from cogip.models import ShellMenu, PoseCurrent


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

    #: :obj:`qtSignal(float, float, float)`:
    #:      Qt signal emitted to update Robot position.
    #:      Parameters are `x`, `y`, `angle`.
    #:
    #:      Connected to :class:`~cogip.robot.Robot`.
    signal_new_robot_position = qtSignal(float, float, float)

    #: :obj:`qtSignal(str)`:
    #:      Qt signal emitted when the next Robot position number is reached.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_new_robot_position_number = qtSignal(str)

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
                logger.debug("ping1")
                line = self.serial_port.readline().rstrip().decode(errors="ignore")
                if line[0] == ">":
                    continue
                try:
                    logger.debug(f"ping2: {line}")
                    menu = ShellMenu.parse_raw(line)
                    logger.debug("ping3")
                    self.signal_new_menu.emit(menu)
                    logger.debug("ping4")
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
                self.serial_port.write(b"_pose\n")

                pose_found = False
                while not self.exiting and not pose_found:
                    line = self.serial_port.readline().rstrip().decode(errors="ignore")
                    try:
                        pose = PoseCurrent.parse_raw(line)
                        self.position_queue.put(pose)
                        pose_found = True
                    except ValidationError:
                        pass
            logger.debug("main_loop: lock released")

        # Close the serial port before exiting the thread
        self.serial_port.close()
