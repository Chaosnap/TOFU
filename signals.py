#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: signals.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import argparse
import logging
import json
import pickle
import os

# create a logger
logger = logging.getLogger("signals")
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
settingsFile = "./settings.json"
parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=False)
namespace = parser.parse_args()
if namespace.settings is not None:
    settingsFile = namespace.settings
settings = None
logger.info("loading settings from file: %s" % (settingsFile))
with open(settingsFile) as fid:
    settings = json.load(fid)
# extract path to settings file
settingsFileLocation = os.path.abspath(settingsFile)
settingsFilePath = os.path.dirname(settingsFileLocation) + "/"

# extracting signals from database
logger.info("extracting signals from signal properties")
signalPropertiesFile = settingsFilePath + settings["parse"]["signalPropertiesFile"]
signal_properties = []
with open(signalPropertiesFile, "rb") as f:
    signal_properties = pickle.load(f)

signals = []
for signal in signal_properties:
    signals.append({"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]})
    # signals.append(int(signal[0]))
