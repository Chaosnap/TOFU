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

TOFU_PATH?=..
VENV?=source $(TOFU_PATH)/tofu_python/bin/activate
SHELL:=$(shell which bash)
LOGLEVEL?=info

NR_SIMULATIONS?=100
NUMBERS:=$(shell seq 1 ${NR_SIMULATIONS})

SIMS:=$(addprefix vcd/aes, ${NUMBERS})
SIMS:=$(addsuffix .vcd, ${SIMS})

TVS:=$(addprefix testvector/testvector, ${NUMBERS})
TVS:=$(addsuffix .tv, ${TVS})

AES_SOURCE_PATH?=aes-vhdl

DPA_SETTINGS_FILE?=settings_example.json

all:
	@echo "make aes_vhdl"
	@echo "make simulate -j numberofcores"
	@echo "make attack"

aes_vhdl: test_enc

simulate: cleansim test_enc $(TVS) $(SIMS)

attack: dpa

dpa:
	$(VENV); python3 dpa_lascar.py --settings $(DPA_SETTINGS_FILE)
	cat generate_testvectors.py | grep key | head -n 1
	
example_aes: clean cleansim
	make simulate -j $(nproc) NR_SIMULATIONS=3000
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example.json --loglevel $(LOGLEVEL)
	make dpa

example_aes_filtered: clean cleansim
	make simulate -j $(nproc) NR_SIMULATIONS=100
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example.json --loglevel $(LOGLEVEL)
	@# generate filtered signals.json
	$(VENV); python3 $(TOFU_PATH)/extractsignalids.py --settings settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example.json --loglevel $(LOGLEVEL)
	make dpa

ntofu:
	$(VENV); python3 $(TOFU_PATH)/ntofu.py --settings ntofu_settings_example.json

ntofu_example_aes: clean cleansim
	make simulate -j $(nproc) NR_SIMULATIONS=3000
	$(VENV); python3 $(TOFU_PATH)/ntofu.py --settings ntofu_settings_example.json
	make dpa DPA_SETTINGS_FILE=ntofu_settings_example.json

clean:
	rm -rf aes-vhdl-work
	rm -f correlation.pdf
	rm -f correlation.h5
	rm -f traces.h5
	rm -f test_enc
	rm -f *test_enc.o
	rm -f signals.json
	rm -f tofu_traces.h5
	rm -f ntofu_traces.h5
	rm -f signal_properties_meta.pickle
	rm -f signal_properties.pickle

cleansim:
	rm -rf testvector/
	rm -rf vcd/

test_enc:
	mkdir -p aes-vhdl-work
	ghdl -i --workdir=aes-vhdl-work $(AES_SOURCE_PATH)/aes.vhdl enc_tb.vhd
	ghdl -m --workdir=aes-vhdl-work test_enc

testvector/testvector%.tv:
	@mkdir -p testvector
	@echo "generating testvector $*"
	@python3 generate_testvectors.py testvector/testvector$*.tv $*

vcd/aes%.vcd: testvector/testvector%.tv test_enc
	@mkdir -p vcd
	@echo "running simulation $*"
	@# The testbench requires key and plaintext as arguments.
	@args=$$(bash .arguments.sh $*); \
	ghdl -r --workdir=aes-vhdl-work test_enc --vcd=vcd/aes$*.vcd $$args --ieee-asserts=disable --stop-time=30ms