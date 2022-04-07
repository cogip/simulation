from enum import IntEnum


class OutputMessageType(IntEnum):
    """
    Kind of messages that can be sent on serial port.
    """

    COMMAND = 0
    """
    A command that will be sent and executed on to the robot."""

    COPILOT_CONNECTED = 1
    """
    Inform the robot that the Copilot is connected.
    """

    COPILOT_DISCONNECTED = 2
    """
    Inform the robot that the Copilot is disconnected.
    """
