import asyncio
from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PositionalActuatorCommand,
    PositionalActuatorEnum,
    ServoCommand,
    ServoEnum,
)

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


# Servos
async def servo_command(planner: "Planner", servo: ServoEnum, command: int) -> float:
    await planner.sio_ns.emit("actuator_command", ServoCommand(id=servo, command=command).model_dump())
    return 0


async def left_cart_in(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_LEFT_CART, 950)


async def left_cart_out(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_LEFT_CART, 400)


async def right_cart_in(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_RIGHT_CART, 50)


async def right_cart_out(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_RIGHT_CART, 600)


async def arm_panel_open(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_ARM_PANEL, 890)


async def arm_panel_close(planner: "Planner") -> float:
    return await servo_command(planner, ServoEnum.LXSERVO_ARM_PANEL, 350)


# Positional Motors
async def positional_motor_command(
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
) -> float:
    await planner.sio_ns.emit("actuator_command", PositionalActuatorCommand(id=motor, command=command).model_dump())
    return 0


async def bottom_lift_down(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_BOTTOM_LIFT, 0)
    return 0


async def bottom_lift_up(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_BOTTOM_LIFT, 1)
    return 0


async def top_lift_down(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_TOP_LIFT, 0)
    return 0


async def top_lift_up(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.MOTOR_TOP_LIFT, 1)
    return 0


async def bottom_grip_left_close(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_LEFT, 0)
    return 0


async def bottom_grip_left_open(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_LEFT, 1)
    return 0


async def bottom_grip_right_close(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_RIGHT, 0)
    return 0


async def bottom_grip_right_open(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_RIGHT, 1)
    return 0


async def top_grip_left_close(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_LEFT, 0)
    return 0


async def top_grip_left_open(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_LEFT, 1)
    return 0


async def top_grip_right_close(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_RIGHT, 0)
    return 0


async def top_grip_right_open(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_RIGHT, 1)
    return 0


async def cart_magnet_left_on(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.CART_MAGNET_LEFT, 0)
    return 0


async def cart_magnet_left_off(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.CART_MAGNET_LEFT, 1)
    return 0


async def cart_magnet_right_on(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.CART_MAGNET_RIGHT, 0)
    return 0


async def cart_magnet_right_off(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.CART_MAGNET_RIGHT, 1)
    return 0


async def pami_arm_close(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_PAMI, 0)
    return 0


async def pami_arm_open(planner: "Planner") -> float:
    await positional_motor_command(planner, PositionalActuatorEnum.ANALOGSERVO_PAMI, 1)
    return 0


# Combined actions
async def bottom_grip_close(planner: "Planner") -> float:
    await asyncio.gather(
        bottom_grip_left_close(planner),
        bottom_grip_right_close(planner),
    )
    return 0


async def bottom_grip_open(planner: "Planner") -> float:
    await asyncio.gather(
        bottom_grip_left_open(planner),
        bottom_grip_right_open(planner),
    )
    return 0


async def top_grip_close(planner: "Planner") -> float:
    await asyncio.gather(
        top_grip_left_close(planner),
        top_grip_right_close(planner),
    )
    return 0


async def top_grip_open(planner: "Planner") -> float:
    await asyncio.gather(
        top_grip_left_open(planner),
        top_grip_right_open(planner),
    )
    return 0


async def cart_in(planner: "Planner") -> float:
    await asyncio.gather(
        left_cart_in(planner),
        right_cart_in(planner),
    )
    return 0


async def cart_out(planner: "Planner") -> float:
    await asyncio.gather(
        left_cart_out(planner),
        right_cart_out(planner),
    )
    return 0


async def cart_magnet_on(planner: "Planner") -> float:
    await asyncio.gather(
        cart_magnet_left_on(planner),
        cart_magnet_right_on(planner),
    )
    return 0


async def cart_magnet_off(planner: "Planner") -> float:
    await asyncio.gather(
        cart_magnet_left_off(planner),
        cart_magnet_right_off(planner),
    )
    return 0
