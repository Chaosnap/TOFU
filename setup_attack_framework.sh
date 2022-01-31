#!/bin/bash
# This file is part of TOFU
#
# TOFU is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2022 (C)
# Technical University of Munich
# TUM Department of Electrical and Computer Engineering
# Chair of Security in Information Technology
# Written by the following authors: Michael Gruber

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
