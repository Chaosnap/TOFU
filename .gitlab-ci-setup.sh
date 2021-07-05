#!/bin/bash

set -e
set -u
set -f
set -o pipefail

# make apt run in non interactive mode
export DEBIAN_FRONTEND=noninteractive

apt update
apt upgrade --assume-yes

#install required tools
apt install --assume-yes make git sudo ghdl python3.8 python3-venv zip clang
