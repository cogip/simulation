#!/bin/bash
set -xe
sudo -v

SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`

# Generate COGIP tools package
(cd .. && python3 setup.py sdist --dist-dir ${SCRIPT_DIR})

DOCKER_BUILDKIT=1 docker build . -f Dockerfile.customize --target beacon -t cogip/raspios:beacon
DOCKER_BUILDKIT=1 docker build . -f Dockerfile.customize --target robot -t cogip/raspios:robot
