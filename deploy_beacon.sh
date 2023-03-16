#!/bin/bash

python setup.py sdist && scp dist/cogip-tools-1.0.0.tar.gz beacon: && ssh beacon sudo python3 -m pip install cogip-tools-1.0.0.tar.gz && ssh beacon sudo systemctl restart server planner

