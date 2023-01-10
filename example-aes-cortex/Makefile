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

NR_SIMULATIONS?=10
NUMBERS:=$(shell seq 1 ${NR_SIMULATIONS})

PICKLES:=$(addprefix vcd/aes, ${NUMBERS})
PICKLES:=$(addsuffix .pickle, ${PICKLES})

SIMS:=$(addprefix vcd/aes, ${NUMBERS})
SIMS:=$(addsuffix .vcd, ${SIMS})

TVS:=$(addprefix testvector/testvector, ${NUMBERS})
TVS:=$(addsuffix .tv, ${TVS})

DPA_SETTINGS_FILE?=settings_example.json

all: correlation.h5 traces.h5

example_aes: clean cleansim
	make all -j $(nproc) NR_SIMULATIONS=300

clean:
	rm -f correlation.pdf
	rm -f correlation.h5
	rm -f traces.h5
	rm -f signals.json
	rm -f tofu_traces.h5
	rm -f signal_properties_meta.pickle
	rm -f signal_properties.pickle

cleansim:
	rm -rf testvector/
	rm -rf vcd/
	make -C aes-c clean

testvector/testvector%.tv :
	@mkdir -p testvector
	@echo "generating testvector $*"
	@$(VENV); python3 generate_testvectors.py testvector/testvector$*.tv $*

vcd/aes%.vcd : testvector/testvector%.tv # aes-c/main.bin
	@mkdir -p vcd
	@#echo "running simulation $*"
	$(VENV); python3 tempeh.py $< $@

$(SIMS) : aes-c/main.bin

aes-c/main.bin :
	make -C aes-c main.bin

correlation.h5 : traces.h5
	$(VENV); python3 dpa_lascar.py --settings $(DPA_SETTINGS_FILE)
	cat generate_testvectors.py | grep key | head -n 1

# new make version 3.8 required due to grouped explicit target
ifneq ($(filter grouped-target,$(.FEATURES)),)

$(PICKLES) signals.json signal_properties.pickle &: $(SIMS) #$(DPA_SETTINGS_FILE) do not change parse related settings
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example.json --loglevel $(LOGLEVEL)

traces.h5 : $(TVS) $(SIMS) $(PICKLES) $(DPA_SETTINGS_FILE) signals.json signal_properties.pickle
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example.json --loglevel $(LOGLEVEL)

else

traces.h5 : $(TVS) $(SIMS) $(DPA_SETTINGS_FILE)
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example.json --loglevel $(LOGLEVEL)

endif