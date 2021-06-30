#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: synthesize.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Lars Tebelmann lars.tebelmann@tum.de, Michael Gruber m.gruber@tum.de
# Date:   11.11.2020
# -------------------------------------------------------------------------------------------------

import logging
import json
import pickle
import argparse
import os.path

# create a logger
logger = logging.getLogger("extractsignalids")
if logger.hasHandlers():
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# loading settings from file
parser = argparse.ArgumentParser(description="Extract signal IDs for given modules and signals. Requires " '"signalsFileNameLiterals" entry')
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=True)
namespace = parser.parse_args()
if namespace.settings is not None:
    settingsFile = namespace.settings
settings = None
logger.info("loading settings from file: %s" % (settingsFile))
with open(settingsFile) as fid:
    settings = json.load(fid)

# extract signals which should be used for synthesis
signals_under_inspection = []
configFileOut = settings["synthesize"]["signalsFileName"]

# catch the error if the file is not defined
try:
    configFile = settings["synthesize"]["signalsFileNameLiterals"]
except KeyError:
    # if not defined in the
    logging.error("You need to specify the file name 'signalsFileNameLiterals' in the settings file.")
    exit(1)

if not os.path.isfile(configFile):
    logger.error("%s not found." % (configFile))
    exit(0)
else:
    logger.info("%s found using signals as specified" % (configFile))
    with open(configFile, "r", encoding="utf-8") as fid:
        signals_under_inspection_names = json.load(fid)

try:
    signals_to_include = signals_under_inspection_names["include"]
    signals_to_exclude = signals_under_inspection_names["exclude"]
except KeyError:
    logging.error("Incompatable format. Use 'exlude'/'include'")
    exit(1)

# case include and exclude
if signals_to_include != [] and signals_to_exclude != []:
    signals_under_inspection_names = signals_to_include
# case only include
elif signals_to_include != []:
    signals_under_inspection_names = signals_to_include
# case only exclude
elif signals_to_exclude != []:
    signals_under_inspection_names = signals_to_exclude
# case whether exclude nor include: ERROR
else:
    logging.error("No signals to include nor to exclude")
    exit(1)

# extracting signals from database
logger.info("extracting signals from signal properties")
signalPropertiesFile = settings["parse"]["signalPropertiesFile"]
signal_properties = []
with open(signalPropertiesFile, "rb") as f:
    signal_properties = pickle.load(f)

# find modules and signals
modules_under_inspection = []
special_signals = [[], []]

for k in signals_under_inspection_names:
    # split into submodules
    tmp = k.split("->")
    if "module" in tmp[-1]:
        # if last part is a module, add module
        modules_under_inspection.append(k)
    else:
        # add signal name
        special_signals[0].append(tmp[-1])
        # add corresponding module
        special_signals[1].append("->".join(tmp[:-1]))

signals = []
for signal in signal_properties:
    # signals.append({"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]})
    signals.append(int(signal[0]))
    if any(signal[3] == v for v in modules_under_inspection):
        # add all signal modules that are tracked entirely
        signals_under_inspection.append(int(signal[0]))
    else:
        # in case of signal (not entire modules)
        # iterate through all modules corresponding to the desired signal (yes, could be done more pythonic...)
        for vdx, v in enumerate(special_signals[1]):
            if signal[3] == v:
                # if the correct module is found, check whether it's the right signal
                if signal[1] == special_signals[0][vdx]:
                    # if module and signal match, add the signal
                    signals_under_inspection.append(int(signal[0]))

# reduce signals to distinct ones
signals_under_inspection = list(set(signals_under_inspection))

# if there are signals to exclude
if signals_to_exclude != []:
    # only exclude
    if signals_to_include == []:
        all_signals = []
        for signal in signal_properties:
            all_signals.append(int(signal[0]))
        all_signals = list(set(all_signals))
        for ids in all_signals:
            if ids in signals_under_inspection:
                all_signals.remove(ids)
        signals_under_inspection = all_signals
    # include and then exclude
    else:
        # find signals to exclude (same as above)
        modules_under_inspection = []
        special_signals = [[], []]
        for k in signals_to_exclude:
            tmp = k.split("->")
            if "module" in tmp[-1]:
                modules_under_inspection.append(k)
            else:
                special_signals[0].append(tmp[-1])
                special_signals[1].append("->".join(tmp[:-1]))
        # find signal ids to exclude (same as above)
        signalid_to_exclude = []
        signals = []
        for signal in signal_properties:
            signals.append(int(signal[0]))
            if any(signal[3] == v for v in modules_under_inspection):
                signalid_to_exclude.append(int(signal[0]))
            else:
                for vdx, v in enumerate(special_signals[1]):
                    if signal[3] == v:
                        if signal[1] == special_signals[0][vdx]:
                            signalid_to_exclude.append(int(signal[0]))
        # exclude signal_ids from signals_under_inspection
        for ids in signalid_to_exclude:
            if ids in signals_under_inspection:
                signals_under_inspection.remove(ids)

# write file
with open(configFileOut, "w", encoding="utf-8") as fid:
    json.dump(signals_under_inspection, fid, ensure_ascii=False, indent=4)
