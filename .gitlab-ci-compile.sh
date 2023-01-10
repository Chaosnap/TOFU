#!/bin/bash

set -e
set -u
set -f
set -o pipefail

pkgver() {
    printf "revision-%s-%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

# compile
rm -rf build
mkdir -p build
mkdir -p tofu_python

make pep selftest VENV=false LOGLEVEL=warning

make example_aes_vhdl NR_SIMULATIONS=3000 VENV=false LOGLEVEL=warning
zip -rq build/vcd-vhdl.zip example-aes-vhdl/vcd
zip -rq build/testvector-vhdl.zip example-aes-vhdl/testvector
cp example-aes-vhdl/correlation.pdf build/correlation-vhdl.pdf
cp example-aes-vhdl/correlation.h5 build/correlation-vhdl.h5
cp example-aes-vhdl/traces.h5 build/traces-vhdl.h5

make example_aes_cortex NR_SIMULATIONS=300 VENV=false LOGLEVEL=warning
zip -rq build/vcd-cortex.zip example-aes-cortex/vcd
zip -rq build/testvector-cortex.zip example-aes-cortex/testvector
cp example-aes-cortex/correlation.pdf build/correlation-cortex.pdf
cp example-aes-cortex/correlation.h5 build/correlation-cortex.h5
cp example-aes-cortex/traces.h5 build/traces-cortex.h5