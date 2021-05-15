import time
from serial import Serial
from threading import Lock
# import ptvsd # Used to debug with VS Code

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot
from pydantic import ValidationError

from cogip import logger
from cogip.models import ShellMenu, RobotState, DynObstacleList
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
        signal_new_dyn_obstacles:
            Qt signal emitted to update dynamic obstacles
        max_parse_attemps:
            Maximum number of attemps to receive the expected data
        last_cycle:
            Record the last cycle to avoid sending the same data several times
    """
    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(ShellMenu)
    signal_new_robot_state: qtSignal = qtSignal(RobotState)
    signal_new_dyn_obstacles: qtSignal = qtSignal(DynObstacleList)
    max_parse_attemps: int = 20
    last_cycle: int = 0

    def __init__(self, uart_device: str, no_wait: bool = False):
        """
        Class constructor.

        Arguments:
            uart_device: Serial port to open and control in this class.
        """

        super(SerialController, self).__init__()
        self.no_wait = no_wait

        # Set to true by the main thread to exit this thread after processing the current line
        self.exiting = False

        # Create the serial port, set its parameters, but do not open it yet
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 115200

        self.menu_has_state_cmd = False
        self.serial_lock = Lock()

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
        self.reload_menu()

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

        if not self.no_wait:
            # Initialization loop
            logger.debug("Waiting for shell mode")
            exit_loop = False
            while not self.exiting and not exit_loop:
                line = self.serial_port.readline().rstrip().decode(errors="ignore")
                if line == "Press Enter to cancel planner start...":
                    exit_loop = True
                self.signal_new_console_text.emit(line)

            self.serial_port.write(b"\n")

        self.reload_menu()

        self.set_shm_key()

        while not self.exiting:
            time.sleep(0.01)
            if not self.menu_has_state_cmd:
                continue
            logger.debug("main_loop: try to acquire lock")
            with self.serial_lock:
                logger.debug("main_loop: lock acquired")

                self.get_state()

            logger.debug("main_loop: lock released")

        # Close the serial port before exiting the thread
        self.serial_port.close()

    def set_shm_key(self):
        """
        Initialize the shared memory segment and send its key to the robot.
        """
        Sensor.init_shm()
        self.serial_port.write(f"_set_shmem_key {Sensor.shm_key}\n".encode())

    def reload_menu(self):
        """
        Get the current menu from the robot and send it to the main window.
        """
        self.menu_has_state_cmd = False

        logger.debug("reload_menu: try to acquire lock")
        with self.serial_lock:
            logger.debug("reload_menu: lock acquired")
            self.serial_port.write(b"_help_json\n")

            while True:
                line = self.serial_port.readline().rstrip().decode(errors="ignore")
                if len(line) == 0:
                    continue
                if line[0] in [">", "_"]:
                    continue
                try:
                    menu = ShellMenu.parse_raw(line)
                    self.signal_new_menu.emit(menu)
                    for entry in menu.entries:
                        if entry.cmd == "_state":
                            self.menu_has_state_cmd = True
                            break
                    break
                except ValidationError:
                    self.signal_new_console_text.emit(line)
        logger.debug("reload_menu: lock released")

    def get_state(self):
        """
        Get position information from the robot and send it to the main window
        and to the robot entity.
        """
        self.serial_port.write(b"_state\n")

        pose_found = False
        attempt = 0
        while (not self.exiting and not pose_found
                and attempt < SerialController.max_parse_attemps):
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if len(line) == 0:
                continue
            if line[0] in [">", "_"]:
                continue
            try:
                state = RobotState.parse_raw(line)
                pose_found = True
                if state.cycle == self.last_cycle:
                    continue
                self.last_cycle = state.cycle
                self.signal_new_robot_state.emit(state)
            except ValidationError:
                attempt += 1
                self.signal_new_console_text.emit(line)
                # print(f"parse failed: {line}")
