from serial import Serial
from threading import Lock
import time

from pydantic import ValidationError

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.tools.lidarpf.dataproxy import LidarData


class LidarSerial(QtCore.QObject):
    """
    This class controls the serial port used to communicate
    with the firmware running on our platform.

    It runs in its own thread.

    Attributes:
        new_data:
            Qt signal emitted when a new data is available
    """

    new_data: qtSignal = qtSignal(list)
    max_parse_attemps: int = 1

    def __init__(self, uart_device: str):
        """
        Class constructor.

        Arguments:
            uart_device: Serial port to open and to control by this class.
        """
        super().__init__()

        # Set to true by the main thread to exit this thread after processing the current line
        self.exiting = False

        # Create the serial port, set its parameters, but do not open it yet
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 115200

        self.serial_lock = Lock()

    def quit(self):
        """
        Request to exit the thread as soon as possible.
        """
        self.exiting = True

    def process_output(self):
        """
        Main loop executed in a thread.

        Process the output of the serial port,
        parse the data and send corresponding information
        """
        self.serial_port.open()

        while not self.exiting:
            time.sleep(0.1)
            self.get_data()

        # Close the serial port before exiting the thread
        self.stop_lidar()
        self.serial_port.close()

    @qtSlot()
    def start_lidar(self):
        """
        Start Lidar.
        """
        with self.serial_lock:
            self.serial_port.write(b"start\n")

    @qtSlot()
    def stop_lidar(self):
        """
        Stop Lidar.
        """
        with self.serial_lock:
            self.serial_port.write(b"stop\n")

    @qtSlot(int)
    def set_filter(self, filter: int):
        """
        Set filter.

        Arguments:
            filter: New filter value.
        """
        with self.serial_lock:
            self.serial_port.write(f"filter {filter}\n".encode())

    def get_data(self):
        """
        Get Lidar data.
        """
        with self.serial_lock:
            self.serial_port.write(b"data\n")

        data_found = False
        attempt = 0
        while (not self.exiting and not data_found
                and attempt < self.max_parse_attemps):
            line = self.serial_port.readline().rstrip().decode(errors="ignore")
            if len(line) == 0:
                continue
            if line[0] == ">":
                continue
            try:
                data = LidarData.parse_raw(line)
                data_found = True
                self.new_data.emit(data)
            except ValidationError:
                attempt += 1
                print(f"parse failed: {line}")
