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
apt install --assume-yes make git sudo ghdl python3.8 python3-venv python3-pip zip clang

BASEDIR=$(pwd)
rm -rf tofu_python
rm -rf lascar.git

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

git clone https://github.com/Ledger-Donjon/lascar lascar.git
cd lascar.git
python3 setup.py install
cd $BASEDIR
rm -rf lascar.git

# workaround lascar lacks psutil
python3 -m  pip install --upgrade psutil