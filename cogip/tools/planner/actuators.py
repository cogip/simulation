from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
    PumpCommand,
    PumpEnum,
    ServoCommand,
    ServoEnum,
)

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


# Pumps
async def pump_command(planner: "Planner", pump: PumpEnum, command: bool) -> float:
    await planner.sio_ns.emit("actuator_command", PumpCommand(id=pump, command=command).model_dump())
    return 0


async def pump_left_on(planner: "Planner") -> float:
    return await pump_command(planner, PumpEnum.PUMP_LEFT_ARM, True)


async def pump_left_off(planner: "Planner") -> float:
    return await pump_command(planner, PumpEnum.PUMP_LEFT_ARM, False)


async def pump_right_on(planner: "Planner") -> float:
    return await pump_command(planner, PumpEnum.PUMP_RIGHT_ARM, True)


async def pump_right_off(planner: "Planner") -> float:
    return await pump_command(planner, PumpEnum.PUMP_RIGHT_ARM, False)


# Servos
async def servo_command(planner: "Planner", servo: ServoEnum, command: int) -> float:
    await planner.sio_ns.emit("actuator_command", ServoCommand(id=servo, command=command).model_dump())
    return 0


async def left_arm_folded(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_LEFT_ARM, 900)


async def left_arm_extended(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_LEFT_ARM, 260)


async def right_arm_folded(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_RIGHT_ARM, 0)


async def right_arm_extended(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_RIGHT_ARM, 666)


async def right_arm_mid(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_RIGHT_ARM, 333)


# Positional Motors
async def positional_motor_command(
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
) -> float:
    await planner.sio_ns.emit("actuator_command", PositionalActuatorCommand(id=motor, command=command).model_dump())
    return 0


async def led_off(planner: "Planner") -> float:
    return await positional_motor_command(planner, PositionalActuatorEnum.ONOFF_LED_PANELS, 0)


async def led_on(planner: "Planner") -> float:
    return await positional_motor_command(planner, PositionalActuatorEnum.ONOFF_LED_PANELS, 1)


async def central_arm_up(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_CENTRAL_LIFT, 100)
    return 2.5


async def central_arm_down(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_CENTRAL_LIFT, -100)
    return 2.5


async def left_arm_up(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.LXMOTOR_LEFT_ARM_LIFT, 100)
    return 0


async def left_arm_down(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.LXMOTOR_LEFT_ARM_LIFT, -100)
    return 0


async def right_arm_up(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.LXMOTOR_RIGHT_ARM_LIFT, 100)
    return 0


async def right_arm_down(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.LXMOTOR_RIGHT_ARM_LIFT, -100)
    return 0
