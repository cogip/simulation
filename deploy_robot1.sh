#!/bin/bash

python setup.py sdist
scp dist/cogip-tools-1.0.0.tar.gz robot1:
ssh robot1 sudo python3 -m pip install cogip-tools-1.0.0.tar.gz
ssh robot1 sudo systemctl restart cogip-copilot cogip-server cogip-planner cogip-dashboard
