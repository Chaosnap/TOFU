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

all: clean kat_hw kat_hd

kat_hw:
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example_kat_hw.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/extractsignalids.py --settings settings_example_kat_hw.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example_kat_hw.json --loglevel $(LOGLEVEL)
	$(VENV); python3 kat.py --settings settings_example_kat_hw.json

kat_hd:
	$(VENV); python3 $(TOFU_PATH)/parse.py --settings settings_example_kat_hd.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/extractsignalids.py --settings settings_example_kat_hd.json --loglevel $(LOGLEVEL)
	$(VENV); python3 $(TOFU_PATH)/synthesize.py --settings settings_example_kat_hd.json --loglevel $(LOGLEVEL)
	$(VENV); python3 kat.py --settings settings_example_kat_hd.json

clean:
	rm -f *.pickle
	rm -f signals.json
	rm -f traces_*.h5