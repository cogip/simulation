The simulation depends on a specific version of `mcu-firmware` which also depends on a specific version of `RIOT`. So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`. 
Do not forget to fetch the submodules after `git clone`:
```bash
git submodule init
git submodule update
```

To setup a new environment, create a virtual env and install the requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Use the following command to build the native version of the firmware:

```bash
make -C submodules/mcu-firmware/applications/cogip2019-cortex BOARD=cogip2019-cortex-native MCUFIRMWARE_OPTIONS=calibration
```

The variable `QUIET=0` can be added to display compilation commands.

The asset files for table and robot are loaded by default in `../models`.
It can be adjusted using command line options (`bin/simulator.py --help` for more information).
The asset's format currently supported is Collada (`.dae`).

Run `bin/simulator.py` to launch the simulator.
