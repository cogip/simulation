import asyncio
from typing import TYPE_CHECKING

from cogip.models.actuators import (
    PumpEnum, PumpCommand,
    ServoEnum, ServoCommand,
    PositionalActuatorEnum, PositionalActuatorCommand
)

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


# Pumps
async def pump_command(robot_id: int, planner: "Planner", pump: PumpEnum, command: bool) -> float:
    await planner._sio_ns.emit("actuator_command", data={
        "robot_id": robot_id,
        "command": PumpCommand(id=pump, command=command).model_dump()
    })
    return 0


async def pump_left_on(robot_id: int, planner: "Planner") -> float:
    return await pump_command(robot_id, planner, PumpEnum.PUMP_LEFT_ARM, True)


async def pump_left_off(robot_id: int, planner: "Planner") -> float:
    return await pump_command(robot_id, planner, PumpEnum.PUMP_LEFT_ARM, False)


async def pump_right_on(robot_id: int, planner: "Planner") -> float:
    return await pump_command(robot_id, planner, PumpEnum.PUMP_RIGHT_ARM, True)


async def pump_right_off(robot_id: int, planner: "Planner") -> float:
    return await pump_command(robot_id, planner, PumpEnum.PUMP_RIGHT_ARM, False)


# Servos
async def servo_command(robot_id: int, planner: "Planner", servo: ServoEnum, command: int) -> float:
    await planner._sio_ns.emit("actuator_command", data={
        "robot_id": robot_id,
        "command": ServoCommand(id=servo, command=command).model_dump()
    })
    return 0


async def cherry_switch_closed(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_BALL_SWITCH, 550)


async def cherry_switch_cake(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_BALL_SWITCH, 936)


async def cherry_switch_launcher(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_BALL_SWITCH, 80)


async def left_arm_folded(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_LEFT_ARM, 900)


async def left_arm_extended(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_LEFT_ARM, 260)


async def right_arm_folded(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_RIGHT_ARM, 0)


async def right_arm_extended(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_RIGHT_ARM, 666)


async def right_arm_mid(robot_id: int, planner: "Planner") -> float:
    return await servo_command(robot_id, planner, ServoEnum.LXSERVO_RIGHT_ARM, 333)


# Positional Motors
async def positional_motor_command(
        robot_id: int,
        planner: "Planner",
        motor: PositionalActuatorEnum,
        command: int) -> float:
    await planner._sio_ns.emit("actuator_command", data={
        "robot_id": robot_id,
        "command": PositionalActuatorCommand(id=motor, command=command).model_dump()
    })
    return 0


async def led_off(robot_id: int, planner: "Planner") -> float:
    return await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ONOFF_LED_PANELS, 0)


async def led_on(robot_id: int, planner: "Planner") -> float:
    return await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ONOFF_LED_PANELS, 1)


async def central_arm_up(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.MOTOR_CENTRAL_LIFT, 100)
    return 2.5 if robot_id == 2 else 3.3


async def central_arm_down(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.MOTOR_CENTRAL_LIFT, -100)
    return 2.5 if robot_id == 2 else 3.3


async def cherry_arm_up(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_ARM, 0)
    return 0  # TO DEFINE


async def cherry_arm_down(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_ARM, 1)
    return 0  # TO DEFINE


async def cherry_esc_on(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(
        robot_id, planner,
        PositionalActuatorEnum.ANALOGSERVO_CHERRY_ESC, planner._properties.esc_speed
    )
    return 0


async def cherry_esc_off(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_ESC, 0)
    return 0


async def cherry_esc_eject(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_ESC, 5)
    return 0


async def cherry_release_down(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_RELEASE, 0)
    return 0


async def cherry_release_up(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.ANALOGSERVO_CHERRY_RELEASE, 1)
    return 0


async def left_arm_up(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.LXMOTOR_LEFT_ARM_LIFT, 100)
    return 0


async def left_arm_down(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.LXMOTOR_LEFT_ARM_LIFT, -100)
    return 0


async def right_arm_up(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.LXMOTOR_RIGHT_ARM_LIFT, 100)
    return 0


async def right_arm_down(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.LXMOTOR_RIGHT_ARM_LIFT, -100)
    return 0


async def cherry_conveyor_on(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(
        robot_id, planner,
        PositionalActuatorEnum.MOTOR_CONVEYOR_LAUNCHER, planner._properties.launcher_speed
    )
    return 0


async def cherry_conveyor_off(robot_id: int, planner: "Planner") -> float:
    await positional_motor_command(robot_id, planner, PositionalActuatorEnum.MOTOR_CONVEYOR_LAUNCHER, 0)
    return 0


# Combined actions
async def action_deliver_on_cake(robot_id: int, planner: "Planner") -> float:
    time_switch_open = 0.6
    time_switch_close = 0.6
    time_release_up = 0.6
    time_release_down = 0.6
    await cherry_switch_cake(robot_id, planner)
    await asyncio.sleep(time_switch_open)
    await cherry_switch_closed(robot_id, planner)
    await asyncio.sleep(time_switch_close)
    await cherry_release_up(robot_id, planner)
    await asyncio.sleep(time_release_up)
    await cherry_release_down(robot_id, planner)
    await asyncio.sleep(time_release_down)
    return await central_arm_up(robot_id, planner)


async def action_launch_start(robot_id: int, planner: "Planner") -> float:
    time_switch_open = 0.6
    time_switch_close = 0.6
    await cherry_conveyor_on(robot_id, planner, 75)
    await cherry_switch_launcher(robot_id, planner)
    await asyncio.sleep(time_switch_open)
    await cherry_switch_closed(robot_id, planner)
    await asyncio.sleep(time_switch_close)
    return time_switch_open + time_switch_close


async def action_launch_stop(robot_id: int, planner: "Planner") -> float:
    await cherry_conveyor_off(robot_id, planner)
    return 0


async def action_aspirate_start(robot_id: int, planner: "Planner") -> float:
    await cherry_esc_on(robot_id, planner)
    await cherry_switch_closed(robot_id, planner)
    time_arm_down = await cherry_arm_up(robot_id, planner)
    await asyncio.sleep(time_arm_down)
    return 0


async def action_aspirate_stop(robot_id: int, planner: "Planner") -> float:
    await cherry_esc_off(robot_id, planner)
    time_arm_up = await cherry_arm_up(robot_id, planner)
    return time_arm_up
