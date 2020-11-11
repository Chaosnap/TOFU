#!/bin/bash
# setup attack framework virtualenv

set -eu -o pipefail
shopt -s nullglob
shopt -s failglob

BASEDIR=$(pwd)
rm -rf attackframework.git

source tofu_python/bin/activate

# Clone Attack-Framework
git clone https://gitlab.lrz.de/TUEISEC-Intern/Attack-Framework.git attackframework.git
cd attackframework.git
# Pick version 1.3.10
git checkout 1.3.10
# Install
python3 setup.py install
cd $BASEDIR
rm -rf attackframework.git
