#!/bin/bash

set -e
set -u
set -f
set -o pipefail

# make apt run in non interactive mode
export DEBIAN_FRONTEND=noninteractive

apt update
apt upgrade --assume-yes

# install required tools
apt install --assume-yes \
make \
git \
sudo \
ghdl \
python3.8 \
python3-venv \
python3-pip \
zip \
clang \
cmake \
pkg-config \
gcc-arm-none-eabi \
binutils-arm-none-eabi

BASEDIR=$(pwd)
rm -rf tofu_python
rm -rf lascar.git
rm -rf unicorn.git

# setup required python packages
python3 -m  pip install --upgrade pip
python3 -m  pip install --upgrade ipython
python3 -m  pip install --upgrade numba
python3 -m  pip install --upgrade autopep8
python3 -m  pip install --upgrade flake8
python3 -m  pip install --upgrade black
python3 -m  pip install --upgrade cython

# fix version clash
python3 -m  pip uninstall pyparsing
python3 -m  pip install pyparsing==2.4.7

# install lascar from git repository
git clone https://github.com/Ledger-Donjon/lascar lascar.git
cd lascar.git
python3 setup.py install
cd $BASEDIR
rm -rf lascar.git

# install unicorn from git repository
git clone https://github.com/unicorn-engine/unicorn unicorn.git
cd unicorn.git
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make install -j$(nproc)
cd ..
cd bindings
python3 const_generator.py python
cd python
python3 setup.py build
python3 setup.py install