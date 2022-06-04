#!/bin/bash
set -xe
sudo -v

SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`

# Generate COGIP tools package
(cd .. && python3 setup.py sdist --dist-dir ${SCRIPT_DIR})

DOCKER_BUILDKIT=1 docker build . -f Dockerfile.customize -t cogip/raspios:custom
