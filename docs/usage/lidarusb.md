# Lidar USB Viewer

This tool displays a graphical view to render data provided by a YDLidar G2 connected to USB port.

After installation (see [Install](../install.md)), the `Lidar USB Viewer` is launched with:
```bash
$ cogip-lidarusb
```

The serial port is detected automatically by the YDLidar SDK, so this tool has no specific options.

## Interface

The graphical interface provides a polar chart and table view.

![View with unfiltered data](../img/lidarusb/lidarusb_unfiltered.png)

![View with filtered data](../img/lidarusb/lidarusb_filtered.png)

### Polar Chart

Two kind of values are drawn on the chart:

- distance values for each degree (in millimeters)

- intensity values for each degree

Below the chart, the `Max Distance` and `Max Intensity` sliders allow to zoom
on the distance and intensity axes.

The `Distance filter` slider can be enabled/disabled using the checkbox.
If disabled, distance values displayed on the charts are raw data.
If enables, a filter is applied to drop corrupted values and
limit the detection to the maximum distance selected by the slider.

### Table

The table on the right of the window presents the same data as the chart but in numeric format.

