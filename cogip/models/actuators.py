from enum import IntEnum

from pydantic import BaseModel, Field

from ..tools.copilot.messages import PB_PumpCommand, PB_ServoCommand


# Actuators common definitions

class ActuatorsKindEnum(IntEnum):
    SERVO = 0
    PUMP = 1


class ActuatorsGroupEnum(IntEnum):
    NO_GROUP = 0
    LEFT_ARM = 1
    RIGHT_ARM = 2
    CENTRAL_ARM = 3


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
    ARM_CENTRAL_BASE = 1
    ARM_CENTRAL_MID = 2
    ARM_CENTRAL_HEAD = 3
    ARM_CENTRAL_LIFT = 5
    ARM_RIGHT_BASE = 9
    ARM_RIGHT_HEAD = 10
    ARM_LEFT_BASE = 11
    ARM_LEFT_HEAD = 12
    STORAGE = 4
    WHEEL = 13


class ServoCommand(BaseModel):
    kind: ActuatorsKindEnum = Field(ActuatorsKindEnum.SERVO, const=True)
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
    ARM_LEFT_PUMP = 0
    ARM_CENTRAL_PUMP = 1
    ARM_RIGHT_PUMP = 2


class PumpCommand(BaseModel):
    kind: ActuatorsKindEnum = Field(ActuatorsKindEnum.PUMP, const=True)
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


class ActuatorsState(BaseModel):
    servos: list[Servo] = []
    pumps: list[Pump] = []
    robot_id: int


ActuatorCommand = ServoCommand | PumpCommand
