#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: ntofu.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de, Florian Kasten
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import ctypes
import time
import numpy as np
from lascar import AbstractContainer, Trace, Hdf5Container
import json
import argparse
import glob
import tueisec
import os
import re

# import binascii


fdir = os.path.dirname(os.path.realpath(__file__))

settings_file = fdir + "/example/settings.json"

parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=False)
namespace = parser.parse_args()
if namespace.settings is not None:
    settings_file = namespace.settings
print("settings file: %s" % settings_file)

with open(settings_file) as f:
    settings = json.load(f)


# sort naturaly not in aphabetic order
def natural_sort_key(s):
    natural_sort_regex = re.compile("([0-9]+)")
    return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]


# globbing for vcd files
files = glob.glob(settings["vcdGlob"])
files = sorted(files, key=natural_sort_key)
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
write_traces = settings["writeTraces"]
writeTracesFormat = settings["format"]
batch_size = settings["writeTracesBatchSize"]
window = settings["window"]
window_from = settings["windowFrom"]
window_to = settings["windowTo"]
valueExtractFunction = settings["valueExtractFunction"]
valueExtractFile = None  # if None, then valueExtractIndex is used, otherwise valueExtract
if valueExtractFunction == "valueExtract":
    valueExtractFile = settings["valueExtractFile"].encode()
use_value_extract = valueExtractFile is not None
write_trace_format = settings["format"]
align = settings["allign"]
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


class AcquisitionSetupToggle(AbstractContainer):
    def __init__(self):
        self.number_of_traces = num_files
        AbstractContainer.__init__(self, self.number_of_traces)

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
            return Trace(leakage, value[0])
        else:
            # index_ttest = int(re.findall(b"aes(.+?)\.vcd", files[index])[0])
            value = np.array([[index]], dtype=np.uint8)
            # print(value)
            return Trace(leakage, value)


aqc = AcquisitionSetupToggle()

# import matplotlib.pyplot as plt
# plt.plot(aqc[0][0])
# plt.show()


# export traces to container
if write_traces:
    if writeTracesFormat == "lascar":
        try:
            hdf5_container._file.close()
        except NameError:
            pass
        hdf5_container = Hdf5Container.export(aqc, trace_file_name, batch_size=batch_size)
    elif writeTracesFormat == "tueisec":
        tueisec.export(aqc, settings)
    else:
        Exception("format not supported")


print("Finished in %f seconds." % (time.perf_counter() - time_start))
