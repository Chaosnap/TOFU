#!/bin/bash
# setup sica_tool python virtualenv

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

git clone https://github.com/Ledger-Donjon/lascar lascar.git
cd lascar.git
python3 setup.py install

cd $BASEDIR

rm -rf lascar.git