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
# Written by the following authors: Michael Gruber

import argparse
import logging
import os
import sys
import h5py
import numpy as np
import importlib.util

# importing helper source file directly
helperRelPath = "../helper.py"
helperAbsPath = os.path.abspath(helperRelPath)
spec = importlib.util.spec_from_file_location("helper", helperAbsPath)
helper = importlib.util.module_from_spec(spec)
sys.modules["helper"] = helper
spec.loader.exec_module(helper)

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
settings = helper.validateSettings(settings, mode="tofu")
settings = helper.prepareSettings(settingsFile, settings, mode="tofu")

# perform kat test
foo = h5py.File(settings["traceFileName"])
leakage = np.array(foo["/leakages"][0])

logger.info(f"leakage {leakage}")

if settings["leakageModel"] == "HammingWeight":
    kat_leakage = np.array([8, 7, 8, 7, 8], dtype=np.uint32)
elif settings["leakageModel"] == "HammingDistance":
    kat_leakage = np.array([1, 1, 1, 1], dtype=np.uint32)
else:
    raise Exception()

leakageModel = settings["leakageModel"]

# check if leakages are equal
if not np.array_equal(leakage, kat_leakage):
    raise Exception(f"kat {leakageModel} failed")
logger.info(f"kat {leakageModel} ok")
