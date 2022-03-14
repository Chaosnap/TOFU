#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
# Written by the following authors: Michael Gruber, Lea Straumann, Lars Tebelmann

import logging
import json
import pickle
import argparse
import os.path
import helper
import re

# loading settings from file
parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=True)
parser.add_argument("-l", "--loglevel", type=str, help="specify loglevel", required=False, default="info")
namespace = parser.parse_args()

# create a logger
logger = logging.getLogger(os.path.basename(__file__))
if logger.hasHandlers():
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# parse loglevel
loglevel = namespace.loglevel
numeric_log_id = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_log_id, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logger.setLevel(numeric_log_id)

# prepare settings dictionary
settingsFile = namespace.settings
logger.info("loading settings from file: %s" % (settingsFile))
settings = helper.loadSettings(settingsFile)
settings = helper.validateSettings(settings)
settings = helper.prepareSettings(settingsFile, settings)


# extract signals which should be used for synthesis
signals_under_inspection = []

if not os.path.isfile(settings["signalsFileNameLiterals"]):
    raise Exception("%s not found." % (settings["signalsFileNameLiterals"]))
else:
    logger.info("using signals as specified in %s" % (settings["signalsFileNameLiterals"]))
    with open(settings["signalsFileNameLiterals"], "r", encoding="utf-8") as fid:
        signals_under_inspection_names = json.load(fid)


if "include" not in signals_under_inspection_names.keys() or "exclude" not in signals_under_inspection_names.keys():
    raise Exception("Incompatable format. Use exlude/include")

# format of signal properties file
# signal_properties.append((signal["numeric_id"], signal["name"], signal["width"], signal["scope"]))

# extracting signals from database
logger.info("extracting signals from signal properties")
signal_properties = []
with open(settings["signalPropertiesFile"], "rb") as f:
    signal_properties = pickle.load(f)

include_signals = []
exclude_signals = []

for include_pattern in signals_under_inspection_names["include"]:
    logger.info(f"processing include pattern: {include_pattern}")

    for signal in signal_properties:
        foo = signal[3] + "->" + signal[1]
        signal_match = re.match(f"{re.escape(include_pattern)}.*", foo)
        if signal_match is not None:
            logger.debug(f"include adding: {signal}")
            include_signals.append(signal)

for exclude_pattern in signals_under_inspection_names["exclude"]:
    logger.info(f"processing exclude pattern: {exclude_pattern}")

    for signal in signal_properties:
        foo = signal[3] + "->" + signal[1]
        signal_match = re.match(f"^{re.escape(exclude_pattern)}.*?", foo)
        if signal_match is not None:
            logger.debug(f"exclude adding: {signal}")
            exclude_signals.append(signal)


include_signals = [i[0] for i in include_signals]
exclude_signals = [i[0] for i in exclude_signals]
signals_under_inspection = list(set(include_signals) - set(exclude_signals))


for signal in signal_properties:
    if signal[0] in signals_under_inspection:
        foo = signal[3] + "->" + signal[1]
        logger.debug(f"inspecting {foo}")

logger.debug(signals_under_inspection)

if not signals_under_inspection:
    raise Exception("no signals to inspect")

# write file
with open(settings["signalsFileName"], "w", encoding="utf-8") as fid:
    json.dump(signals_under_inspection, fid, ensure_ascii=False, indent=4)
