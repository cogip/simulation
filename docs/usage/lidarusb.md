# Lidar USB Viewer

This tool displays a graphical view to render data provided by a HLS-LFCD2 Lidar connected to USB port.

After installation (see [Install](../install.md)), the `Lidar USB Viewer` is launched with:
```bash
$ lidarusb
```

The `Lidar USB Viewer` requires a HLS-LFCD2 Lidar to be connected to an USB port using a Serial-USB converter.

By default, the serial ports are scanned, and if found, the first port will be used.

If the right USB port is not automatically detected, it can be specified using command line option.

##  Command line options

```text
$ lidarusb --help
Usage: lidarusb [OPTIONS] [UART]

  Starts the Lidar USB View tool.

Arguments:
  [UART]  The UART port to use  [default: (dynamic)]

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.
```
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

