from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

ANALOGSERVO_BOTTOM_GRIP_LEFT: PB_PositionalActuatorEnum
ANALOGSERVO_BOTTOM_GRIP_RIGHT: PB_PositionalActuatorEnum
ANALOGSERVO_PAMI: PB_PositionalActuatorEnum
ANALOGSERVO_TOP_GRIP_LEFT: PB_PositionalActuatorEnum
ANALOGSERVO_TOP_GRIP_RIGHT: PB_PositionalActuatorEnum
BOOL_SENSOR: PB_ActuatorsTypeEnum
BOTTOM_GRIP_LEFT: PB_BoolSensorEnum
BOTTOM_GRIP_RIGHT: PB_BoolSensorEnum
CART_MAGNET_LEFT: PB_PositionalActuatorEnum
CART_MAGNET_RIGHT: PB_PositionalActuatorEnum
DESCRIPTOR: _descriptor.FileDescriptor
LXSERVO_ARM_PANEL: PB_ServoEnum
LXSERVO_LEFT_CART: PB_ServoEnum
LXSERVO_RIGHT_CART: PB_ServoEnum
MAGNET_LEFT: PB_BoolSensorEnum
MAGNET_RIGHT: PB_BoolSensorEnum
MOTOR_BOTTOM_LIFT: PB_PositionalActuatorEnum
MOTOR_TOP_LIFT: PB_PositionalActuatorEnum
POSITIONAL: PB_ActuatorsTypeEnum
SERVO: PB_ActuatorsTypeEnum
TOP_GRIP_LEFT: PB_BoolSensorEnum
TOP_GRIP_RIGHT: PB_BoolSensorEnum

class PB_ActuatorCommand(_message.Message):
    __slots__ = ["positional_actuator", "servo"]
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    SERVO_FIELD_NUMBER: _ClassVar[int]
    positional_actuator: PB_PositionalActuatorCommand
    servo: PB_ServoCommand
    def __init__(self, servo: _Optional[_Union[PB_ServoCommand, _Mapping]] = ..., positional_actuator: _Optional[_Union[PB_PositionalActuatorCommand, _Mapping]] = ...) -> None: ...

class PB_ActuatorState(_message.Message):
    __slots__ = ["bool_sensor", "positional_actuator", "servo"]
    BOOL_SENSOR_FIELD_NUMBER: _ClassVar[int]
    POSITIONAL_ACTUATOR_FIELD_NUMBER: _ClassVar[int]
    SERVO_FIELD_NUMBER: _ClassVar[int]
    bool_sensor: PB_BoolSensor
    positional_actuator: PB_PositionalActuator
    servo: PB_Servo
    def __init__(self, servo: _Optional[_Union[PB_Servo, _Mapping]] = ..., positional_actuator: _Optional[_Union[PB_PositionalActuator, _Mapping]] = ..., bool_sensor: _Optional[_Union[PB_BoolSensor, _Mapping]] = ...) -> None: ...

class PB_BoolSensor(_message.Message):
    __slots__ = ["id", "state"]
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    id: PB_BoolSensorEnum
    state: bool
    def __init__(self, id: _Optional[_Union[PB_BoolSensorEnum, str]] = ..., state: bool = ...) -> None: ...

class PB_PositionalActuator(_message.Message):
    __slots__ = ["command", "id", "is_blocked"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    IS_BLOCKED_FIELD_NUMBER: _ClassVar[int]
    command: int
    id: PB_PositionalActuatorEnum
    is_blocked: bool
    def __init__(self, is_blocked: bool = ..., id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., command: _Optional[int] = ...) -> None: ...

class PB_PositionalActuatorCommand(_message.Message):
    __slots__ = ["command", "id"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    command: int
    id: PB_PositionalActuatorEnum
    def __init__(self, id: _Optional[_Union[PB_PositionalActuatorEnum, str]] = ..., command: _Optional[int] = ...) -> None: ...

class PB_Servo(_message.Message):
    __slots__ = ["command", "id", "is_blocked", "position"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    IS_BLOCKED_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    command: int
    id: PB_ServoEnum
    is_blocked: bool
    position: int
    def __init__(self, is_blocked: bool = ..., id: _Optional[_Union[PB_ServoEnum, str]] = ..., position: _Optional[int] = ..., command: _Optional[int] = ...) -> None: ...

class PB_ServoCommand(_message.Message):
    __slots__ = ["command", "id", "time"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    command: int
    id: PB_ServoEnum
    time: int
    def __init__(self, id: _Optional[_Union[PB_ServoEnum, str]] = ..., command: _Optional[int] = ..., time: _Optional[int] = ...) -> None: ...

class PB_ActuatorsTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_ServoEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_PositionalActuatorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class PB_BoolSensorEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
