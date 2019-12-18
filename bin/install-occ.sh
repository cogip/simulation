#!/bin/bash

# This script installs OpenCascade Community Edition and Python-OCC from git sources

# Tested on:
#   - Ubuntu 18.04 (bionic) - Python 3.6
#   - Ubuntu 19.04 (disco) - Python 3.7
#   - Ubuntu 19.10 (eoan) - Python 3.7
#   - Debian 9 (stretch) - Python 3.5
#   - Debian 10 (buster) - Python 3.7

#set -x

# This directory will contain venv, source, build and install directories
ROOT_DIR=~/cogip/opencascade

PYQT_VERSION=5.12.3
#PYQT_VERSION=5.13.2
# Open CASCACE Community Edition: https://github.com/tpaviot/oce
OCE_TAG=OCE-0.18.3 # Last OCE release
# pythonocc: https://github.com/tpaviot/pythonocc-core
PYTHONOCC_TAG=0.18.2 # Simulation code requires python-occ>=0.18.2
CMAKE_VERSION=3.16.1 # Master branch of pythonocc requires cmake>=3.14, not yet available in distros

# Enable/disable installation steps
CREATE_VENV=0
INSTALL_CMAKE=0
INSTALL_OCE=0
INSTALL_PYTHONOCC=1
RUN_TESTS=1

### DO NOT EDIT AFTER THIS LINE ###

DEB_PKG_REQUIRED="wget build-essential git python3 python3-dev python3-pip python3-venv swig libfreetype6-dev freeglut3-dev tcl-dev tk-dev"
PYTHON_PKG_REQUIRED="six PyQt5==${PYQT_VERSION} psutil serial"

ROOT_DIR=$(readlink -f ${ROOT_DIR})
VENV_DIR=${ROOT_DIR}/venv
SOURCE_DIR=${ROOT_DIR}/source
BUILD_DIR=${ROOT_DIR}/build
INSTALL_DIR=${ROOT_DIR}/install

# Check not root
if [[ $(id -u) -eq 0 ]] ; then
    echo "Don't run this script as root"
    exit 1
fi

# Check not already in venv
if [[ -v VIRTUAL_ENV ]] ;
then
    echo "Already in a virtual-env, please deactivate it before running this script."
    exit 1
fi

# Check required Debian packages
echo "=== Checking Debian packages"
deb_pkg_missing=""
for deb_pkg in ${DEB_PKG_REQUIRED}
do
    dpkg -s ${deb_pkg} &> /dev/null
    not_installed=$?
    if [[ ${not_installed} -ne 0 ]] ; then
        deb_pkg_missing="${deb_pkg_missing} ${deb_pkg}"
    fi
done

set -e

if [[ -n "${deb_pkg_missing}" ]] ; then
    echo "Some Debian packages are missing. Please run the following command and restart this script:"
    echo "sudo apt install -y ${deb_pkg_missing}"
    exit 1
fi

mkdir -p ${SOURCE_DIR} ${BUILD_DIR} ${INSTALL_DIR}

# Create Python virtual-env
if [[ ${CREATE_VENV} -eq 0 ]] ;
then
    echo "=== Skipping Python virtual-env creation"
    source ${ROOT_DIR}/venv/bin/activate
else
    echo "=== Create Python virtual-env"
    rm -rf ${VENV_DIR}
    python3 -m venv ${ROOT_DIR}/venv
    source ${ROOT_DIR}/venv/bin/activate

    # Install Python packages
    echo "===  Install Python packages"
    pip install wheel
    pip install ${PYTHON_PKG_REQUIRED}
fi


# Install CMake
CMAKE_ROOT_NAME=cmake-${CMAKE_VERSION}-Linux-x86_64
CMAKE_ARCHIVE=${INSTALL_DIR}/${CMAKE_ROOT_NAME}.tar.gz
CMAKE_INSTALL_DIR=${INSTALL_DIR}/${CMAKE_ROOT_NAME}
if [[ ${INSTALL_CMAKE} -eq 0 ]] ;
then
    echo "=== Skipping CMake installation"
else
    echo "=== Install CMake ${CMAKE_VERSION}"
    rm -rf ${INSTALL_DIR}/cmake-*
    wget --show-progress https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/${CMAKE_ROOT_NAME}.tar.gz -O ${CMAKE_ARCHIVE}
    tar xf ${CMAKE_ARCHIVE} -C ${INSTALL_DIR}
    echo "export PATH=${CMAKE_INSTALL_DIR}/bin:\${PATH}" >> ${VENV_DIR}/bin/activate
    export PATH=${CMAKE_INSTALL_DIR}/bin:${PATH}
fi

# Install OCE
OCE_SOURCE_DIR=${SOURCE_DIR}/oce
OCE_BUILD_DIR=${BUILD_DIR}/oce
OCE_INSTALL_DIR=${INSTALL_DIR}/oce
if [[ ${INSTALL_OCE} -eq 0 ]] ;
then
    echo "=== Skipping OCE installation"
else
    echo "=== Install OCE"
    rm -rf ${OCE_SOURCE_DIR} ${OCE_BUILD_DIR} ${OCE_INSTALL_DIR}
    git clone git://github.com/tpaviot/oce.git -b ${OCE_TAG} ${OCE_SOURCE_DIR}
    cmake -Wno-dev -S ${OCE_SOURCE_DIR} -B ${OCE_BUILD_DIR} -DOCE_DRAW:BOOL=on -DOCE_MULTITHREAD_LIBRARY:STRING=TBB -DOCE_INSTALL_PREFIX=${OCE_INSTALL_DIR}
    make -C ${OCE_BUILD_DIR} -j$(nproc) install
    if [[ ${RUN_TESTS} -eq 1 ]] ;
    then
        make -C ${OCE_BUILD_DIR} test
    fi
    echo "export LD_LIBRARY_PATH=${OCE_INSTALL_DIR}/lib:\${LD_LIBRARY_PATH}" >> ${VENV_DIR}/bin/activate
    export LD_LIBRARY_PATH=${OCE_INSTALL_DIR}/lib:${LD_LIBRARY_PATH}
fi


# Install python-occ
PYTHONOCC_SOURCE_DIR=${SOURCE_DIR}/pythonocc
PYTHONOCC_BUILD_DIR=${BUILD_DIR}/pythonocc
if [[ ${INSTALL_PYTHONOCC} -eq 0 ]] ;
then
    echo "=== Skipping pythonocc installation"
else
    echo "=== Install pythonocc"
    rm -rf ${PYTHONOCC_SOURCE_DIR} ${PYTHONOCC_BUILD_DIR} ${PYTHONOCC_INSTALL_DIR}
    git clone git://github.com/tpaviot/pythonocc-core.git -b ${PYTHONOCC_TAG} ${PYTHONOCC_SOURCE_DIR}
    cmake -Wno-dev -S ${PYTHONOCC_SOURCE_DIR} -B ${PYTHONOCC_BUILD_DIR} -DOCE_INCLUDE_PATH=${OCE_INSTALL_DIR}/include/oce -DOCE_LIB_PATH=${OCE_INSTALL_DIR}/lib
    make -C ${PYTHONOCC_BUILD_DIR} -j$(nproc) install
    if [[ ${RUN_TESTS} -eq 1 ]] ;
    then
        (cd ${PYTHONOCC_SOURCE_DIR}/test && python run_tests.py)
    fi
fi

echo "=== pythonocc environment set up successfully"
echo "Load it with 'source ${VENV_DIR}/bin/activate'"
