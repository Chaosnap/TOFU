#!/bin/bash

set -e
set -u
set -f
set -o pipefail

pkgver() {
    printf "revision-%s-%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

#compile
rm -rf build
mkdir -p build

make venv
make pep
source tofu_python/bin/activate
make example_aes NR_SIMULATIONS=3000

zip -r build/vcd.zip example-aes-vhdl/vcd
zip -r build/testvector.zip example-aes-vhdl/testvector
cp example-aes-vhdl/correlation.pdf build/
cp example-aes-vhdl/correlation.pdf build/
cp example-aes-vhdl/correlation.h5 build/
cp example-aes-vhdl/traces.h5 build/
