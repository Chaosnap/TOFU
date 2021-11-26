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

import value
import argparse
import logging
import json
import os
import glob
import numpy as np
import pickle
import time
from lascar import AbstractContainer, Trace, Hdf5Container
import tueisec
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
settings = helper.validateSettings(settings)
settings = helper.prepareSettings(settingsFile, settings)


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDistanceFromBitString(x, y):
    assert len(x) == len(y)
    if len(x) == 1:
        return x != y
    else:
        return sum(a != b for a, b in zip(x, y))


def hammingWeightFromInt(x):
    return bin(x).count("1")


def hammingDistanceFromInt(x, y):
    return hammingWeightFromInt(x ^ y)


# extracting signals from database
logger.info("extracting signals from signal properties")
signal_properties = []
with open(settings["signalPropertiesFile"], "rb") as f:
    signal_properties = pickle.load(f)

signals = []
for signal in signal_properties:
    # signals.append({"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]})
    signals.append(int(signal[0]))

# reduce signals to distinct ones
signals = list(set(signals))

# extract signals which shoul be used for synthesis
signals_under_inspection = []
if not os.path.isfile(settings["signalsFileName"]):
    logger.info("no signals configured generating standard signals.json")
    with open(settings["signalsFileName"], "w", encoding="utf-8") as fid:
        json.dump(signals, fid, ensure_ascii=False, indent=4)
        signals_under_inspection = signals
else:
    logger.info("%s found using signals as specified" % (settings["signalsFileName"]))
    with open(settings["signalsFileName"], "r", encoding="utf-8") as fid:
        signals_under_inspection = json.load(fid)


# extract the numeric ids under inspection
# numeric_ids_under_inspection = [i["numeric_id"] for i in signals_under_inspection]
numeric_ids_under_inspection = signals_under_inspection
# ids can appear in several scopes so reduce them
settings["numeric_ids_under_inspection"] = list(set(numeric_ids_under_inspection))

# hardcode or not ???
settings["reloadNumericIds"] = True

# globbing for pickle files
pickleFiles = glob.glob(settings["pickleGlob"])

# extract the number of traces
simulation_trace_max = len(pickleFiles)
logger.info("processing: %d traces" % (simulation_trace_max))


# Then the AbstractContainer:
class AcquisitionSetupToggle(AbstractContainer):
    def __init__(self, settings):
        """
        :param number_of_traces: only required argument for the constructor of an AbstractContainer
        """

        # store the assumed leakage model
        self.leakage = settings["leakageModel"]
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            pass
        else:
            raise Exception("undefined leakage model: %s" % self.leakage)

        self.window = settings["window"]
        self.windowFrom = settings["windowFrom"]
        self.windowTo = settings["windowTo"]

        # value extract function
        self.valueExtract = getattr(value, settings["valueExtractFunction"])

        # signals which should be inspected
        self.numeric_ids_under_inspection = numeric_ids_under_inspection
        self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)
        self.reload_numeric_ids = settings["reloadNumericIds"]

        # extract signal properties
        self.signalPropertiesFile = settings["signalPropertiesFile"]
        with open(self.signalPropertiesFile, "rb") as f:
            self.signal_properties = pickle.load(f)
        self.signal_properties = [{"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]} for signal in self.signal_properties]

        signals = [i["numeric_id"] for i in self.signal_properties]
        signals = set(signals)
        # reduce signals to distinct ones
        logger.info("traces consist from %d signals" % (len(signals)))

        # globbing for pickle files
        self.pickleGlob = settings["pickleGlob"]
        self.pickleFiles = glob.glob(self.pickleGlob)
        self.pickleFiles = sorted(self.pickleFiles, key=helper.natural_sort_key)
        # print(self.pickleGlob)

        self.number_of_traces = len(self.pickleFiles)

        # extract the simulation time stamps
        with open(self.pickleFiles[0], "rb") as f:
            self.simulation_time_steps = pickle.load(f)
        self.simulation_time_steps = list(set([i[0] for i in self.simulation_time_steps]))
        self.simulation_time_steps.sort()
        self.simulation_time_to_index = {i[1]: i[0] for i in enumerate(self.simulation_time_steps)}
        self.simulation_index_to_time = {i[0]: i[1] for i in enumerate(self.simulation_time_steps)}
        self.simulation_time_max = self.simulation_time_steps[-1]
        logger.info("traces consist from %d sample points in time" % (len(self.simulation_time_steps)))

        self.numeric_id_to_width = {i["numeric_id"]: i["width"] for i in self.signal_properties}

        self.allign = settings["allign"]
        self.downsample = settings["downsample"]

        AbstractContainer.__init__(self, self.number_of_traces)

    def generate_trace(self, index):
        """
        generate_trace is the only method needed by AcquisitionSetup to work properly
        :param index: index of trace, not used here.
        :return:  Trace with leakage from oscilloscope, and value from the dut plaintext/ciphertext
        """
        # set lascar log level
        self.logger.setLevel(numeric_log_id)

        self.index = index

        time_start = time.time()
        self.logger.info("capturing trace: %d" % (index))

        if self.reload_numeric_ids:
            self.logger.info("reloading numeric ids")
            with open(settings["signalsFileName"], "r", encoding="utf-8") as fid:
                self.numeric_ids_under_inspection = json.load(fid)
                self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)

        # horizontal mode assemmble state from changes and derive leakage
        # fetch all updates
        logger.info("extracting state updates from picklefile")
        updates = None
        with open(self.pickleFiles[index], "rb") as f:
            updates = pickle.load(f)

        # extract value from pickle
        self.updates = updates
        # print(updates)
        value = self.valueExtract(self)

        if self.allign:
            # extract the simulation time stamps
            self.simulation_time_steps = list(set([i[0] for i in updates]))
            self.simulation_time_steps.sort()
            self.simulation_time_max = self.simulation_time_steps[-1]
            logger.info("trace consists from %d sample points in time" % (len(self.simulation_time_steps)))

        ###################################################################################################################################
        # slow slow slow remap this to something performant
        ###################################################################################################################################
        # input  : updates                               type: list of tuples
        # input  : self.simulation_time_to_index              type: dictonary int to int mapping
        # input  : self.windowFrom                            type: integer
        # input  : self.windowTo                              tpye: integer
        # input  : self.numeric_ids_under_inspection_set      type: set of integer
        # output : leakage                                    type: list of integers

        if self.allign:
            samples = int(np.floor_divide(self.simulation_time_max, self.downsample))
            leakage = np.zeros((samples,), dtype=np.uint32)
        else:
            # extract the leakage
            leakage = np.zeros((len(self.simulation_time_steps),), dtype=np.uint32)

        # umbauen ummappen auf signale die benutzt werden
        state = [0 for i in self.numeric_id_to_width.values()]

        logger.info("iterating through all state updates")
        logger.info("performing %d updates" % (len(updates)))

        nextval_index = 0
        nextval_index_old = 0
        toggles = 0

        # perform updates inside the loop
        for update in updates:

            if self.allign:
                # binning of updates
                nextval_index = int(np.floor_divide(update[0], self.downsample))
            else:
                nextval_index = self.simulation_time_to_index[update[0]]

            numeric_id = update[1]
            nextval = update[2]

            # das bremst aus wie noch was
            # check if signal is tracked
            if numeric_id not in self.numeric_ids_under_inspection_set:
                continue

            # bottleneck
            # logger.debug("simulation_time: %d index: %d  numeric_id: %d nextval: %s" % (update[0], nextval_index, numeric_id, nextval))

            if nextval_index != nextval_index_old:

                # this extracts the hamming weight
                if self.leakage == "HammingWeight":
                    leakage[nextval_index_old : nextval_index + 1] = sum(state)
                elif self.leakage == "HammingDistance":
                    # calculate the hamming distance
                    leakage[nextval_index_old : nextval_index + 1] = toggles
                    toggles = 0
                else:
                    raise Exception("undefined leakage model: %s" % self.leakage)

                nextval_index_old = nextval_index

            if self.leakage == "HammingWeight":
                state[numeric_id] = hammingWeightFromInt(nextval)
            elif self.leakage == "HammingDistance":
                toggles += hammingDistanceFromInt(state[numeric_id], nextval)
                state[numeric_id] = nextval
            else:
                raise Exception("undefined leakage model: %s" % self.leakage)

        # perform the last update after the loop
        if self.leakage == "HammingWeight":
            # this extracts the hamming weight
            leakage[nextval_index_old : nextval_index + 1] = sum(state)
            # ignore first point
            leakage = leakage[1:]
        elif self.leakage == "HammingDistance":
            # calculate the hamming distance
            leakage[nextval_index_old : nextval_index + 1] = toggles
            # ignore first point
            leakage = leakage[1:]
        else:
            raise Exception("undefined leakage model: %s" % self.leakage)

        ###################################################################################################################################

        if (self.windowFrom is not None or self.windowTo is not None) and self.window is True:
            logger.info("extracting window from leakage %d:%d" % (self.windowFrom, self.windowTo))
            leakage = leakage[self.windowFrom : self.windowTo]

        time_finish = time.time()
        logger.info("capturing trace took %f seconds" % (time_finish - time_start))

        return Trace(leakage, value)


# create our acquisition setup
aqc = AcquisitionSetupToggle(settings)
# set lascar log level
aqc.logger.setLevel(numeric_log_id)

# export traces to container
if settings["writeTraces"]:
    if settings["format"] == "lascar":
        try:
            hdf5_container._file.close()
        except NameError:
            pass
        hdf5_container = Hdf5Container.export(aqc, settings["traceFileName"], batch_size=settings["writeTracesBatchSize"])
    elif settings["format"] == "tueisec":
        tueisec.export(aqc, settings, settingsFileLocation=settings["settingsFileLocation"])
    else:
        Exception("format not supported")


# print("trace 0:", aqc[0])
# print("trace 10:", aqc[10])

# so kann man plotten
# plt.plot(aqc[0][0])
# plt.show()

# verwendung mit externem tool
# aqc.generate_trace(0)


logger.info("synthesize traces from pickles finished")
