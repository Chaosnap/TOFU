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
