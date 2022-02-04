from serial import Serial
import time

from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot


class LidarSerial(QtCore.QObject):
    """
    This class controls the serial port used to communicate with the robot.
    Its main purpose is to get the shell menu to update the interface,
    get the robot position to update its position, and send the commands
    on the serial port.

    It runs in its own thread.

    Attributes:
        new_frame:
            Qt signal emitted when a new frame is available
    """

    new_data: qtSignal = qtSignal(bytes)

    def __init__(self, uart_device: str):
        """
        Class constructor.

        Arguments:
            uart_device: Serial port to open and control in this class.
        """
        super().__init__()
        self.exiting = False
        self.serial_port = Serial()
        self.serial_port.port = uart_device
        self.serial_port.baudrate = 230400

    def quit(self):
        """
        Request to exit the thread as soon as possible.
        """
        self.exiting = True

    @qtSlot()
    def start_lidar(self):
        """
        Start Lidar.
        """
        self.serial_port.write(b"b")

    @qtSlot()
    def stop_lidar(self):
        """
        Stop Lidar.
        """
        self.serial_port.write(b"e")

    def process_output(self):
        """
        Main loop executed in a thread.

        Process the output of the serial port,
        parse the data and send corresponding information
        """
        self.serial_port.open()
        self.serial_port.write(b'b')

        init_time = time.perf_counter_ns()
        start_time = None
        while not self.exiting:
            frame_bytes = self.serial_port.read(1)
            if start_time is None:
                start_time = time.perf_counter_ns()
                print(f"startup_time = {(start_time-init_time)/1000/1000/1000:.3f}s")

            if frame_bytes != b'\xfa':
                continue
            frame_bytes += self.serial_port.read(41)

            index = frame_bytes[1] - 0xA0
            if index == 0:
                end_time = time.perf_counter_ns()
                read_time = end_time - start_time
                start_time = end_time
                print(f"Read time: {read_time/1000/1000/1000:.3f}")

            # Check frame integrity
            checksum = sum([frame_bytes[i] for i in range(40)])
            checksum = 0xFF - (checksum & 0xFF)
            if checksum != frame_bytes[40]:
                print(f"Indexes {index * 6:3d}-{index * 6 + 6:3d}: bad checksum")
                continue

            self.new_data.emit(frame_bytes)

        self.serial_port.write(b'e')
