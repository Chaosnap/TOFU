#!/bin/bash
# setup tofu python virtualenv

set -eu -o pipefail
shopt -s nullglob
shopt -s failglob

BASEDIR=$(pwd)

python3 -m venv tofu_python
source tofu_python/bin/activate
python3 -m  pip install --upgrade pip
python3 -m  pip install --upgrade ipython
python3 -m  pip install --upgrade numpy
python3 -m  pip install --upgrade autopep8

python3 -m  pip install --upgrade cython

python3 -m  pip install --upgrade PyOpenGL
python3 -m  pip install --upgrade PyOpenGL_accelerate
python3 -m  pip install --upgrade PyQt5

git clone https://github.com/Ledger-Donjon/lascar lascar.git
cd lascar.git
python3 setup.py install

# Clone Attack-Framework
git clone https://gitlab.lrz.de/TUEISEC-Intern/Attack-Framework.git attackframework.git
cd attackframework.git
# Pick version 1.3.10
git checkout 1.3.10
# Install
python3 setup.py install

cd $BASEDIR

rm -rf lascar.git
rm -rf attackframework.git
