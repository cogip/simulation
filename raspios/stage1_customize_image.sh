#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
source ${SCRIPT_DIR}/common.sh

# Generate COGIP tools package
(cd .. && uv build --sdist --out-dir ${SCRIPT_DIR})
cp -f ../.python-version ../pyproject.toml .

DOCKER_BUILDKIT=1 docker build --progress plain . -f Dockerfile.customize --target beacon -t cogip/raspios:beacon
DOCKER_BUILDKIT=1 docker build --progress plain . -f Dockerfile.customize --target robot -t cogip/raspios:robot
DOCKER_BUILDKIT=1 docker build --progress plain . -f Dockerfile.customize --target pami -t cogip/raspios:pami

rm -f .python-version pyproject.toml cogip_tools-*.tar.gz
