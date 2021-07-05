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

# selftest
make venv
make pep
make selftest

# aes example
make example_aes NR_SIMULATIONS=3000
zip -rq build/vcd.zip example-aes-vhdl/vcd
zip -rq build/testvector.zip example-aes-vhdl/testvector
cp example-aes-vhdl/correlation.pdf build/
cp example-aes-vhdl/correlation.pdf build/
cp example-aes-vhdl/correlation.h5 build/
cp example-aes-vhdl/traces.h5 build/
