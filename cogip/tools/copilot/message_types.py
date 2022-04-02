from enum import IntEnum


class InputMessageType(IntEnum):
    """
    Kind of messages that can be received on serial port.
    """

    MENU = 0
    """
    A menu message, indicating that the shell menu has changed
    and providing the new menu.
    """

    RESET = 1
    """
    A reset message, indicating the reboot has just booted.
    """

    STATE = 2
    """
    A state message containing the current state of the robot.
    """


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
