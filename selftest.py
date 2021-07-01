#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: synthesize.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import logging
from lascar.container import Hdf5Container
import numpy as np

# create a logger
logger = logging.getLogger("selftest")
if logger.hasHandlers():
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

tofu_file_name = "example/tofu_traces.h5"
ntofu_file_name = "example/ntofu_traces.h5"

tofu_container = Hdf5Container(tofu_file_name)
ntofu_container = Hdf5Container(ntofu_file_name)

tofu_traces = np.array(tofu_container.leakages)
ntofu_traces = np.array(ntofu_container.leakages)

# check if traces are equal
if not np.array_equal(tofu_traces, ntofu_traces):
    raise Exception("simple example traces failed")
logger.info("simple example traces passed")

tofu_values = np.array(tofu_container.values)
ntofu_values = np.array(ntofu_container.values)

# check if values are equal
if not np.array_equal(tofu_values, ntofu_values):
    raise Exception("simple example values failed")
logger.info("simple example values passed")

tofu_file_name = "example-aes-vhdl/tofu_traces.h5"
ntofu_file_name = "example-aes-vhdl/ntofu_traces.h5"

tofu_container = Hdf5Container(tofu_file_name)
ntofu_container = Hdf5Container(ntofu_file_name)

tofu_traces = np.array(tofu_container.leakages)
ntofu_traces = np.array(ntofu_container.leakages)

# check if traces are equal
if not np.array_equal(tofu_traces, ntofu_traces):
    raise Exception("aes example traces failed")
logger.info("aes example traces passed")

tofu_values = np.array(tofu_container.values)
ntofu_values = np.array(ntofu_container.values)

# check if values are equal
if not np.array_equal(tofu_values, ntofu_values):
    raise Exception("aes example values failed")
logger.info("aes example values passed")
