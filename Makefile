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

VENV?=source tofu_python/bin/activate
NRPOC:=$(shell nproc)
SHELL:=$(shell which bash)
LOGLEVEL?=info

all:
	@echo "ich bin eine katze und weiß von nichts"

venv:
	@[ -d tofu_python ] || bash setup_tofu_python.sh

venvfake: venvclean
	mkdir -p tofu_python/bin
	touch tofu_python/bin/activate

venv_lascar: venv
	bash setup_lascar.sh

venv_attack_framework: venv
	bash setup_attack_framework.sh

engine:
	make -C engine

example: clean venv
	make -C example all LOGLEVEL=$(LOGLEVEL)

example_aes_vhdl: clean venv
	make -C example-aes-vhdl clean cleansim example_aes LOGLEVEL=$(LOGLEVEL)

example_aes_vhdl_filtered: clean venv
	make -C example-aes-vhdl clean cleansim example_aes_filtered LOGLEVEL=$(LOGLEVEL)

ntofu_example_aes_vhdl: clean venv engine
	make -C example-aes-vhdl clean cleansim ntofu_example_aes LOGLEVEL=$(LOGLEVEL)

example_aes_cortex: clean venv
	make -C example-aes-cortex clean cleansim example_aes LOGLEVEL=$(LOGLEVEL)

kat: clean venv
	make -C example-kat clean all LOGLEVEL=$(LOGLEVEL)

selftest: venv engine
	$(VENV); bash selftest.sh

pep: venv
	$(VENV); black ./

pep_check: venv
	$(VENV); black --check  --diff .

clean:
	make -C example clean
	make -C example-aes-vhdl clean
	make -C example-aes-vhdl cleansim
	make -C example-aes-cortex clean
	make -C example-aes-cortex cleansim
	make -C example-kat clean
	make -C engine clean
	rm -rf __pycache__

venvclean:
	rm -rf tofu_python

.PHONY: engine