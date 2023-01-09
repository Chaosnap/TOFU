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
import h5py
import numpy as np


def load_hdf5_file(file_name):
    with h5py.File(file_name, "r") as fid:
        leakages = np.array(fid["/leakages"])
        values = np.array(fid["/values"])
    return (leakages, values)


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

###################################################################################################
tofu_file_name = "example/tofu_traces.h5"
ntofu_file_name = "example/ntofu_traces.h5"

(tofu_traces, tofu_values) = load_hdf5_file(tofu_file_name)
(ntofu_traces, ntofu_values) = load_hdf5_file(ntofu_file_name)

# check if traces are equal
if not np.array_equal(tofu_traces, ntofu_traces):
    raise Exception("simple example traces failed")
logger.info("simple example traces passed")

# check if values are equal
if not np.array_equal(tofu_values, ntofu_values):
    raise Exception("simple example values failed")
logger.info("simple example values passed")

###################################################################################################
tofu_file_name = "example-aes-vhdl/tofu_traces.h5"
ntofu_file_name = "example-aes-vhdl/ntofu_traces.h5"

(tofu_traces, tofu_values) = load_hdf5_file(tofu_file_name)
(ntofu_traces, ntofu_values) = load_hdf5_file(ntofu_file_name)

# check if traces are equal
if not np.array_equal(tofu_traces, ntofu_traces):
    raise Exception("aes example traces failed")
logger.info("aes example traces passed")

# check if values are equal
if not np.array_equal(tofu_values, ntofu_values):
    raise Exception("aes example values failed")
logger.info("aes example values passed")
