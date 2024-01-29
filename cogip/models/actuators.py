from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field

from ..tools.copilot.messages import PB_PositionalActuatorCommand, PB_PumpCommand, PB_ServoCommand

# Actuators common definitions

class ActuatorsKindEnum(IntEnum):
    SERVO = 0
    PUMP = 1
    POSITIONAL = 2


class ActuatorsGroupEnum(IntEnum):
    NO_GROUP = 0


class ActuatorBase(BaseModel):
    group: ActuatorsGroupEnum = Field(
        ActuatorsGroupEnum.NO_GROUP,
        title="Group",
        description="Actuators group"
    )
    order: int = Field(
        0, ge=0,
        title="Order",
        description="Order in group"
    )
    enabled: bool = Field(
        False, title="Enabled",
        description="An actuator is enabled if it has been initialized with its current value"
    )


# Servo related definitions

class ServoEnum(IntEnum):
    LXSERVO_BALL_SWITCH = 1
    LXSERVO_RIGHT_ARM = 2
    LXSERVO_LEFT_ARM = 4


class ServoCommand(BaseModel):
    kind: Literal[ActuatorsKindEnum.SERVO] = ActuatorsKindEnum.SERVO
    id: ServoEnum = Field(
        ...,
        title="Id",
        description="Servo identifier"
    )
    command: int = Field(
        0, ge=0, le=999,
        title="Position Command",
        description="Current servo position command"
    )

    def pb_copy(self, message: PB_ServoCommand) -> None:
        message.id = self.id
        message.command = self.command


class Servo(ActuatorBase, ServoCommand):
    position: int = Field(
        0, ge=0, le=999,
        title="Position",
        description="Current servo position"
    )


# Pump related definitions

class PumpEnum(IntEnum):
    PUMP_RIGHT_ARM = 0
    PUMP_LEFT_ARM = 1


class PumpCommand(BaseModel):
    kind: Literal[ActuatorsKindEnum.PUMP] = ActuatorsKindEnum.PUMP
    id: PumpEnum = Field(
        ...,
        title="Id",
        description="Pump identifier"
    )
    command: bool = Field(
        False,
        title="Pump Command",
        description="Current pump command"
    )

    def pb_copy(self, message: PB_PumpCommand) -> None:
        message.id = self.id
        message.command = self.command


class Pump(ActuatorBase, PumpCommand):
    activated: bool = Field(
        False,
        title="Activated",
        description="Current pump state"
    )
    under_pressure: bool = Field(
        False,
        title="Under pressure",
        description="Is pump under pressure"
    )


# Positional Actuators related definitions

class PositionalActuatorEnum(IntEnum):
    MOTOR_CENTRAL_LIFT = 0
    MOTOR_CONVEYOR_LAUNCHER = 1
    ONOFF_LED_PANELS = 2
    ANALOGSERVO_CHERRY_ARM = 3
    ANALOGSERVO_CHERRY_ESC = 4
    ANALOGSERVO_CHERRY_RELEASE = 5
    LXMOTOR_RIGHT_ARM_LIFT = 6
    LXMOTOR_LEFT_ARM_LIFT = 7


class PositionalActuatorCommand(BaseModel):
    kind: Literal[ActuatorsKindEnum.POSITIONAL] = ActuatorsKindEnum.POSITIONAL
    id: PositionalActuatorEnum = Field(
        ...,
        title="Id",
        description="Positional Actuator identifier"
    )
    command: int = Field(
        0, ge=-100, le=999,
        title="Position Command",
        description="Current positional actuator position command"
    )

    def pb_copy(self, message: PB_PositionalActuatorCommand) -> None:
        message.id = self.id
        message.command = self.command


class PositionalActuator(ActuatorBase, PositionalActuatorCommand):
    pass


class ActuatorsState(BaseModel):
    servos: list[Servo] = []
    pumps: list[Pump] = []
    positional_actuators: list[PositionalActuator] = []
    robot_id: int


ActuatorCommand = ServoCommand | PumpCommand | PositionalActuatorCommand
