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
# Written by the following authors: Michael Gruber, Florian Kasten

import ctypes
import time
import numpy as np
import argparse
import glob
import tueisec
import os
import logging
import helper


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
settings = helper.validateSettings(settings, mode="ntofu")
settings = helper.prepareSettings(settingsFile, settings, mode="ntofu")
fdir = os.path.dirname(os.path.realpath(__file__))


# globbing for vcd files
files = glob.glob(settings["vcdGlob"])
files = sorted(files, key=helper.natural_sort_key)
files = [i.encode() for i in files]
num_files = len(files)

inspected_signals_file_name = settings["signalsFileNameLiterals"]
if inspected_signals_file_name is not None:
    inspected_signals_file_name = inspected_signals_file_name.encode()

leakage_model = settings["leakageModel"]

if leakage_model not in ["HammingWeight", "HammingDistance"]:
    raise Exception("undefined leakage model: %s" % leakage_model)
use_hamming_weight = leakage_model == "HammingWeight"


trace_file_name = settings["traceFileName"]
window = settings["window"]
window_from = settings["windowFrom"]
window_to = settings["windowTo"]
valueExtractFunction = settings["valueExtractFunction"]
valueExtractFile = None  # if None, then valueExtractIndex is used, otherwise valueExtract
if valueExtractFunction == "valueExtract":
    valueExtractFile = settings["valueExtractFile"]
    valueExtractFile = valueExtractFile.encode()
use_value_extract = valueExtractFile is not None
write_trace_format = settings["format"]
align = settings["align"]
downsample = ctypes.c_uint64(int(settings["downsample"]))

lib = ctypes.CDLL(fdir + "/engine/build/library.so")
lib.SetupParser(use_hamming_weight, inspected_signals_file_name, align, downsample, valueExtractFile)

time_start = time.perf_counter()


def parse_file(name):
    num_files_ref = ctypes.c_size_t(0)
    leakages = ctypes.POINTER(ctypes.POINTER(ctypes.c_int64))()
    leakages_count = ctypes.POINTER(ctypes.c_size_t)()
    extracted_values = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))()
    extracted_values_count = ctypes.c_size_t(0)
    lib.ParseFiles(name, ctypes.byref(num_files_ref), ctypes.byref(leakages), ctypes.byref(leakages_count), ctypes.byref(extracted_values), ctypes.byref(extracted_values_count))
    assert num_files_ref.value == 1
    leakage = np.ctypeslib.as_array(leakages[0], shape=(leakages_count[0],))
    return leakage, extracted_values, extracted_values_count.value


class AcquisitionSetupToggle:
    def __init__(self):
        self.number_of_traces = num_files

    def generate_trace(self, index):
        assert index < self.number_of_traces

        leakage, extracted_values, extracted_values_count = parse_file(files[index])

        if (window_from is not None or window_to is not None) and window is True:
            leakage = leakage[window_from:window_to]

        if use_value_extract:
            assert extracted_values_count > 0
            # print(extracted_values_count)
            max_len = max([int(np.ceil(len(extracted_values[0][i]) / 8)) for i in range(0, extracted_values_count)])
            value = np.zeros((extracted_values_count, max_len), dtype=np.uint8)
            for i in range(0, extracted_values_count):
                ev = extracted_values[0][i]
                value[i] = np.frombuffer(int(ev, 2).to_bytes(max_len, byteorder="big"), dtype=np.uint8)
                # print(extracted_values[0])
                # print(binascii.hexlify(bytearray(list(value[0]))))

            # return Trace(leakage, value)
            # bug ?
            return (leakage, value[0])
        else:
            # index_ttest = int(re.findall(b"aes(.+?)\.vcd", files[index])[0])
            value = np.array([index], dtype=np.uint32)
            # print(value)
            return (leakage, value)

    def __getitem__(self, key):
        return self.generate_trace(key)

    def __len__(self):
        return self.number_of_traces


aqc = AcquisitionSetupToggle()

# import matplotlib.pyplot as plt
# plt.plot(aqc[0][0])
# plt.show()


# export traces to container
if settings["writeTraces"]:
    if settings["format"] == "lascar":
        helper.lascarHDF5Export(aqc, settings["traceFileName"], writeTracesBatchSize=settings["writeTracesBatchSize"], logger=logger)
    elif settings["format"] == "tueisec":
        tueisec.export(aqc, settings, settingsFileLocation=settings["settingsFileLocation"])
    else:
        Exception("format not supported")


print("Finished in %f seconds." % (time.perf_counter() - time_start))
