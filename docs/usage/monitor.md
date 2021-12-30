# Monitor

The monitor is used to monitor the robot behavior during the game.
It it connected to `Copilot` embedded in the robot through Socket.IO protocol.

The monitor provides a graphical interface, featuring:

  * a 3D view of the table (in yellow) and the robot (in green)

  * a menu giving access to the firmware's shell menu

  * a button to add obstacles (in grey), move and resize them

  * save and load obstacles using JSON files

  * visualization of ToF (red dots) and LIDAR (bleu dots) sensors detections

  * visualization of obstacles detected in the firmware (in transparent red)

  * charts window to visualize calibration data

![GUI Overview](../img/monitor/gui_overview.png)

![Charts View](../img/monitor/charts_view.png)

## Command line options

```bash
$ monitor --help
Usage: monitor [URL]

  Launch COGIP Monitor.

Arguments:
  [URL]  URL to Copilot socket.io/web server  [env var: COPILOT_URL; default: http://copilot]
```

!!! note "Environnement variables can be set in the `.env` file."

## Launch the monitor

To connect the `Monitor` to the `Copilot` running on the same developmnet PC, run:

```bash
monitor http://localhost:8080
```

To connect the `Monitor` to the `Copilot` running on the Raspberry Pi in the robot, run:

```bash
monitor http://copilot
```

!!! note "Adapt URL and port depending on `Copilot` configuration"
