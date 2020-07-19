import sys
import re
import math
from queue import Queue
from serial import Serial
import ptvsd # Used to debug with VS Code

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal as qtSignal
from PyQt5.QtCore import pyqtSlot as qtSlot

from cogip import logger
from cogip.automaton import Automaton

class SerialController(QtCore.QObject):
    """SerialController class

    This class controls the serial port used to communicate with the robot.

    It is run in its own thread.
    
    Each line written by the robot is parsed and analized. 
    Extracted information is sent via Qt signals to other modules like :class:`~cogip.automaton.Automaton`,
    :class:`~cogip.mainwindow.MainWindow` and :class:`~cogip.robot.Robot`

    These classes also send information to control the robot by wrtiing to its serial port.
    """

    #: :obj:`qtSignal(str)`:
    #:      Qt signal emitted to log messages in UI console.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_new_console_text = qtSignal(str)

    #: :obj:`qtSignal(str)`:
    #:      Qt signal emitted to transition the Automaton state.
    #:      Acts like a proxy to emit signals from their string name.
    #:
    #:      Connected to :class:`~cogip.automaton.Automaton`.
    signal_new_trigger = qtSignal(str)

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
            position_queue (Queue): Queue containing robot position, filled by :class:`~cogip.serialcontroller.SerialController`
        """

        QtCore.QObject.__init__(self)
        self.position_queue = position_queue

        # Record last position to send a position only once
        self.last_position = (-1, -1, -1)

         # Set to true by the main thread to exit this thread after processing the current line
        self.exiting = False
        
        ROBOT_OBJECT_PATTERN = '@robot@'
        POSE_CURRENT_PATTERN = '@pose_current@'
        float_regex = "-?\d*\.\d+"
        self.p = re.compile(f"({ROBOT_OBJECT_PATTERN}),(\d+),\d+,({POSE_CURRENT_PATTERN}),({float_regex}),({float_regex}),({float_regex})")

        # Create the serial port, set its parameters, but do not open it yet
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 115200

        self.commands = {
            "waiting_calibration_mode": b"\n",
            "menu_calibration_planner": b'pc\n',
            "menu_calibration_speed_pid": b'cs\n',
            "menu_calibration_pos_pid": b'cp\n',
            "quit_menu": b'q\n',
            "planner_go_to_next_position": b'n\n',
            "speed_pid_linear_speed_charac": b'l\n',
            "speed_pid_angular_speed_charac": b'a\n',
            "pos_pid_speed_linear_kp": b'a\n'
        }


    def quit(self):
        """Request to exit the thread as soon as possible.
        """
        self.exiting = True

    @qtSlot(str)
    def slot_send_command(self, command):
        bytes_to_send = self.commands.get(command)
        if not bytes_to_send:
            logger.warning(f"Unknown command: {command}")
            return
        self.signal_new_console_text.emit(f"==> write '{bytes_to_send.decode().strip()}'")
        self.serial_port.write(bytes_to_send)

    def process_output(self):
        """Main loop executed in a thread.
        Process the output of the serial port, parse the data and send corresponding information
        """
        # try:
        #     ptvsd.debug_this_thread()
        # except:
        #     pass

        # Open the serial port.
        # In simulation, it also starts the native firmware
        self.serial_port.open()
        
        while not self.exiting:
            line = self.serial_port.readline().rstrip()
            try:
                if line == b"Press Enter to enter calibration mode...":
                    self.signal_new_trigger.emit("trigger_waiting_calibration_mode")
                elif line.startswith(b"platform: Start shell"):
                    self.signal_new_trigger.emit("trigger_menu_main")
                elif line in [b"planner: Controller has reach final position.", b"ctrl: New mode: CTRL_MODE_STOP"]:
                    self.signal_new_trigger.emit("trigger_position_reached")
                elif line.startswith(b"Position index: "):
                    self.signal_new_robot_position_number.emit(line.decode().rpartition(' ')[-1])
                else:
                    m = self.p.match(line.decode())
                    if m:
                        x = float(m[4])
                        y = float(m[5])
                        angle = float(m[6])

                        new_position = (x, y, angle)
                        if new_position != self.last_position:
                            self.position_queue.put(new_position)
                            self.last_position = new_position

                self.signal_new_console_text.emit(line.decode())

            except UnicodeDecodeError:
                # Ignore the line in case of decoding error
                logger.warning(f"Decode error: {line}")

        # Close the serial port before exiting the thread
        self.serial_port.close()
