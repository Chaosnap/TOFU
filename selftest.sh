#!/bin/bash

set -e
set -u
set -f
set -o pipefail

make clean

# generate tofu traces
python3 parse.py --settings example/settings_example.json
python3 synthesize.py --settings example/settings_example.json --loglevel warning
mv example/traces.h5 example/tofu_traces.h5

# generate ntofu traces
python3 ntofu.py --settings example/settings_example.json
mv example/traces.h5 example/ntofu_traces.h5

# generate aes simulation traces
make -C example-aes-vhdl cleansim simulate NR_SIMULATIONS=10

# generate tofu traces
python3 parse.py --settings example-aes-vhdl/settings_example.json
python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
mv example-aes-vhdl/traces.h5 example-aes-vhdl/tofu_traces.h5

# generate ntofu traces
make -C example-aes-vhdl/ ntofu
mv example-aes-vhdl/traces.h5 example-aes-vhdl/ntofu_traces.h5

python3 selftest.py