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
async def pump_command(robot_id: int, planner: "Planner", pump: PumpEnum, command: bool) -> float:
    await planner._sio_ns.emit(
        "actuator_command",
        data={
            "robot_id": robot_id,
            "command": PumpCommand(id=pump, command=command).model_dump(),
        },
    )
    return 0


# Servos
async def servo_command(robot_id: int, planner: "Planner", servo: ServoEnum, command: int) -> float:
    await planner._sio_ns.emit(
        "actuator_command",
        data={
            "robot_id": robot_id,
            "command": ServoCommand(id=servo, command=command).model_dump(),
        },
    )
    return 0


async def left_arm_close(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_LEFT_ARM, 0)


async def left_arm_open(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_LEFT_ARM, 999)


# Positional Motors
async def positional_motor_command(
    robot_id: int,
    planner: "Planner",
    motor: PositionalActuatorEnum,
    command: int,
) -> float:
    await planner._sio_ns.emit(
        "actuator_command",
        data={
            "robot_id": robot_id,
            "command": PositionalActuatorCommand(id=motor, command=command).model_dump(),
        },
    )
    return 0


async def analogservo_bottom_arm_left_close(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(
        robot_id,
        planner,
        PositionalActuatorEnum.ANALOGSERVO_BOTTOM_ARM_LEFT,
        0,
    )
    return 0


async def analogservo_bottom_arm_left_open(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(
        robot_id,
        planner,
        PositionalActuatorEnum.ANALOGSERVO_BOTTOM_ARM_LEFT,
        1,
    )
    return 0
