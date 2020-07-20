The simulation depends on a specific version of `mcu-firmware` which also depend on a specific version of `RIOT`. So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`. 

To setup a working environment, first follow the `README.md` from `mcu-firwmare`.

Then execute `bin/install-occ.sh` (help in included in the file, modify `ROOTDIR` variable to specify this installation directory, `~/cogip/opencascade` by default) to setup the Python environment required to launch `simulator.py`.

Finally, load the new environment (`source ~/cogip/opencascade/venv/bin/activate`).

Use the following command to build the native version of the firmaware:

```bash
make -C submodules/mcu-firmware/applications/cogip2019-cortex BOARD=cogip2019-cortex-native MCUFIRMWARE_OPTIONS=calibration
```

The variable `QUIET=0` can be added to display compilation commands.

The model files for table and robot are loaded by default in `../models`.
It can be adjusted using command line options (`bin/simulator.py --help` for more information).

Run `bin/simulator.py` to launch the simulator.
