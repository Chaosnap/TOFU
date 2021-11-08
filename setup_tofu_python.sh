#!/bin/bash
# setup tofu python virtualenv

set -eu -o pipefail
shopt -s nullglob
shopt -s failglob

BASEDIR=$(pwd)
rm -rf tofu_python
rm -rf lascar.git

python3 -m venv tofu_python
source tofu_python/bin/activate
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