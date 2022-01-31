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

set -e
set -u
set -f
set -o pipefail

# generate tofu traces
python3 parse.py --settings example/settings_example.json  --loglevel warning
python3 synthesize.py --settings example/settings_example.json --loglevel warning
mv example/traces.h5 example/tofu_traces.h5

# generate ntofu traces
python3 ntofu.py --settings example/settings_example.json
mv example/traces.h5 example/ntofu_traces.h5

# generate aes simulation traces
make -C example-aes-vhdl cleansim simulate NR_SIMULATIONS=10

# build ntofu engine
make engine

# generate tofu traces
python3 parse.py --settings example-aes-vhdl/settings_example.json  --loglevel warning
python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
mv example-aes-vhdl/traces.h5 example-aes-vhdl/tofu_traces.h5

# generate ntofu traces
make -C example-aes-vhdl/ ntofu
mv example-aes-vhdl/traces.h5 example-aes-vhdl/ntofu_traces.h5

python3 selftest.py