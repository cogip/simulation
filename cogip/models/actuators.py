from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from cogip.protobuf import PB_PositionalActuatorCommand, PB_ServoCommand

# Actuators common definitions


class ActuatorsKindEnum(IntEnum):
    SERVO = 0
    POSITIONAL = 1


class ActuatorsGroupEnum(IntEnum):
    NO_GROUP = 0


class ActuatorBase(BaseModel):
    group: ActuatorsGroupEnum = Field(
        ActuatorsGroupEnum.NO_GROUP,
        title="Group",
        description="Actuators group",
    )
    order: int = Field(
        0,
        ge=0,
        title="Order",
        description="Order in group",
    )
    enabled: bool = Field(
        False,
        title="Enabled",
        description="An actuator is enabled if it has been initialized with its current value",
    )


# Servo related definitions


class ServoEnum(IntEnum):
    LXSERVO_LEFT_CART = 0
    LXSERVO_RIGHT_CART = 1
    LXSERVO_ARM_PANEL = 2


class ServoCommand(BaseModel):
    kind: Literal[ActuatorsKindEnum.SERVO] = ActuatorsKindEnum.SERVO
    id: ServoEnum = Field(
        ...,
        title="Id",
        description="Servo identifier",
    )
    command: int = Field(
        0,
        ge=0,
        le=999,
        title="Position Command",
        description="Current servo position command",
    )

    @field_validator("kind", mode="before")
    @classmethod
    def validate_kind(cls, v: str) -> ActuatorsKindEnum:
        try:
            value = ActuatorsKindEnum[v]
        except KeyError:
            try:
                value = ActuatorsKindEnum(v)
            except Exception:
                raise ValueError("Not a ActuatorsKindEnum")
        if value != ActuatorsKindEnum.SERVO:
            raise ValueError("Not ActuatorsKindEnum.SERVO value")
        return value

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: str) -> ServoEnum:
        try:
            return ServoEnum[v]
        except KeyError:
            try:
                return ServoEnum(v)
            except Exception:
                raise ValueError("Not a ServoEnum")

    def pb_copy(self, message: PB_ServoCommand) -> None:
        message.id = self.id
        message.command = self.command


class Servo(ActuatorBase, ServoCommand):
    position: int = Field(
        0,
        ge=0,
        le=999,
        title="Position",
        description="Current servo position",
    )


# Positional Actuators related definitions


class PositionalActuatorEnum(IntEnum):
    MOTOR_BOTTOM_LIFT = 0
    MOTOR_TOP_LIFT = 1
    ANALOGSERVO_BOTTOM_GRIP_LEFT = 2
    ANALOGSERVO_BOTTOM_GRIP_RIGHT = 3
    ANALOGSERVO_TOP_GRIP_LEFT = 4
    ANALOGSERVO_TOP_GRIP_RIGHT = 5
    CART_MAGNET_LEFT = 6
    CART_MAGNET_RIGHT = 7
    ANALOGSERVO_PAMI = 8


class PositionalActuatorCommand(BaseModel):
    kind: Literal[ActuatorsKindEnum.POSITIONAL] = ActuatorsKindEnum.POSITIONAL
    id: PositionalActuatorEnum = Field(..., title="Id", description="Positional Actuator identifier")
    command: int = Field(
        0,
        ge=-100,
        le=999,
        title="Position Command",
        description="Current positional actuator position command",
    )

    @field_validator("kind", mode="before")
    @classmethod
    def validate_kind(cls, v: str) -> ActuatorsKindEnum:
        try:
            value = ActuatorsKindEnum[v]
        except KeyError:
            try:
                value = ActuatorsKindEnum(v)
            except Exception:
                raise ValueError("Not a ActuatorsKindEnum")
        if value != ActuatorsKindEnum.POSITIONAL:
            raise ValueError("Not ActuatorsKindEnum.POSITIONAL value")
        return value

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: str) -> PositionalActuatorEnum:
        try:
            return PositionalActuatorEnum[v]
        except KeyError:
            try:
                return PositionalActuatorEnum(v)
            except Exception:
                raise ValueError("Not a PositionalActuatorEnum")

    def pb_copy(self, message: PB_PositionalActuatorCommand) -> None:
        message.id = self.id
        message.command = self.command


class PositionalActuator(ActuatorBase, PositionalActuatorCommand):
    pass


class ActuatorsState(BaseModel):
    servos: list[Servo] = []
    positional_actuators: list[PositionalActuator] = []
    robot_id: int


ActuatorCommand = ServoCommand | PositionalActuatorCommand
