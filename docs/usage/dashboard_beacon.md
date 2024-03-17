# Beacon Dashboard

The `Beacon Dashboard` is a web site displayed on the touchscreens
embedded the central beacon. It provides a menu and a dashboard to monitor all robots,
and give access to the dashboard of each robot.

The web server can also be accessed from any devices (PC, smartphones)
connected to the same network.

The web server listen on port `8080`.

To access to robot dashboards, the beacon dashboard considers that robot hostnames are `robot1` to `robotN`, resolved by the DNS server or defined in `/etc/hosts` and the dashboard ports are `8080 + robot_id`.
