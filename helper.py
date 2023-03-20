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

import os
import json
import re
import time
import sys
import h5py
import logging
import importlib.util


def loadSettings(settingsFile):
    with open(settingsFile) as fid:
        settings = json.load(fid)

    return settings


def validateSettings(settings, mode="tofu"):
    requiredKeys = []
    if mode == "tofu":
        requiredKeys.append("vcdGlob")
        requiredKeys.append("pickleGlob")
        requiredKeys.append("signalsFileNameLiterals")
        requiredKeys.append("signalsFileName")
        requiredKeys.append("signalPropertiesFile")
        requiredKeys.append("leakageModel")
        requiredKeys.append("window")
        requiredKeys.append("windowFrom")
        requiredKeys.append("windowTo")
        requiredKeys.append("valueExtractFunction")
        requiredKeys.append("writeTraces")
        requiredKeys.append("writeTracesBatchSize")
        requiredKeys.append("traceFileName")
        requiredKeys.append("align")
        requiredKeys.append("downsample")
        requiredKeys.append("format")
    elif mode == "ntofu":
        requiredKeys.append("vcdGlob")
        requiredKeys.append("signalsFileNameLiterals")
        requiredKeys.append("leakageModel")
        requiredKeys.append("window")
        requiredKeys.append("windowFrom")
        requiredKeys.append("windowTo")
        requiredKeys.append("valueExtractFunction")
        # requiredKeys.append("valueExtractFile")
        requiredKeys.append("writeTraces")
        requiredKeys.append("writeTracesBatchSize")
        requiredKeys.append("traceFileName")
        requiredKeys.append("align")
        requiredKeys.append("downsample")
        requiredKeys.append("format")
        if settings["valueExtractFunction"] != "valueExtractIndex":
            requiredKeys.append("valueExtractFile")
    else:
        raise Exception(f"mode {mode} not supported us either tofu or ntofu")

    for i in requiredKeys:
        if i not in settings.keys():
            raise Exception(f"You screwed up your settings is missing {i}")

    return settings


def prepareSettings(settingsFile, settings, mode="tofu"):
    # extract path to settings file
    settingsFileLocation = os.path.abspath(settingsFile)
    settingsFilePath = os.path.dirname(settingsFileLocation) + "/"

    # translate all paths to relativ paths
    settings["vcdGlob"] = settingsFilePath + settings["vcdGlob"]
    settings["traceFileName"] = settingsFilePath + settings["traceFileName"]
    settings["settingsFilePath"] = settingsFilePath
    settings["settingsFileLocation"] = settingsFileLocation

    if settings["signalsFileNameLiterals"] is not None:
        settings["signalsFileNameLiterals"] = settingsFilePath + settings["signalsFileNameLiterals"]
    else:
        settings["signalsFileNameLiterals"] = None

    if mode == "tofu":
        settings["pickleGlob"] = settingsFilePath + settings["pickleGlob"]
        settings["signalPropertiesFile"] = settingsFilePath + settings["signalPropertiesFile"]
        settings["signalsFileName"] = settingsFilePath + settings["signalsFileName"]

        if settings["valueExtractFunction"] != "valueExtractIndex":
            valueExtractFile = settingsFilePath + "value.py"
            valueExtractFunction = settings["valueExtractFunction"]

            if not os.path.isfile(valueExtractFile):
                raise Exception(f"value.py is missing {valueExtractFile}")

            settings["valueExtractFile"] = valueExtractFile
            spec = importlib.util.spec_from_file_location("value", settings["valueExtractFile"])
            value = importlib.util.module_from_spec(spec)
            sys.modules["value"] = value
            spec.loader.exec_module(value)
            try:
                getattr(value, settings["valueExtractFunction"])
            except AttributeError:
                raise Exception(f"function {valueExtractFunction} not found in {valueExtractFile}")

    elif mode == "ntofu":
        if "valueExtractFile" in settings.keys():
            settings["valueExtractFile"] = settingsFilePath + settings["valueExtractFile"]

    else:
        raise Exception(f"mode {mode} not supported us either tofu or ntofu")

    return settings


def natural_sort_key(s):
    # sort naturally not in aphabetic order
    natural_sort_regex = re.compile("([0-9]+)")
    return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]


def progressbar(iterable, prefix="", size=100, logger=None):
    len_iterable = len(iterable)
    start_time = time.time()

    def update(index):
        if logger is not None and logger.level < logging.WARNING:
            logger.info("-" * 10)
            return

        elapsed_time = time.time() - start_time
        percent = (index / len_iterable) * 100
        estimated_time = elapsed_time if index == len_iterable else 0 if percent == 0 else (100 - percent) * (elapsed_time / percent)
        progress = int(size * index / len_iterable)
        status = "%s[%s%s] %i/%i %.1f%% %.1fs" % (prefix, "#" * progress, "-" * (size - progress), index, len_iterable, percent, estimated_time)
        try:
            status = status.ljust(os.get_terminal_size(0)[0], " ")
        except OSError:
            status = status.ljust(150, " ")
        status += "\r"
        sys.stdout.write(status)
        sys.stdout.flush()

    update(0)
    for i, item in enumerate(iterable):
        yield i, item
        update(i + 1)

    if logger is None or logger.level >= logging.WARNING:
        sys.stdout.write("\n")
        sys.stdout.flush()


def lascarHDF5Export(aqc, traceFileName, writeTracesBatchSize=None, logger=None):
    if os.path.isfile(traceFileName):
        if logger is None:
            print("file %s already exists, overwriting..." % (traceFileName))
        else:
            logger.warning("file %s already exists, overwriting..." % (traceFileName))
    filehandle = h5py.File(traceFileName, mode="w")

    FHleakages = None
    FHvalues = None

    n_traces = len(aqc)

    # implement batched trace write here

    for i, _ in progressbar(range(n_traces), logger=logger):
        leakage, value = aqc[i]
        if i == 0:
            FHleakages = filehandle.create_dataset("leakages", (n_traces, leakage.shape[0]), dtype=leakage.dtype)
            FHvalues = filehandle.create_dataset("values", (n_traces, value.shape[0]), dtype=value.dtype)

        FHleakages[i, :] = leakage
        FHvalues[i, :] = value

    filehandle.close()
