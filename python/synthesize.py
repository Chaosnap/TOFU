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
import os.path
import glob
import numpy as np
import h5py
import re
import pickle
import importlib
import time
import matplotlib.pyplot as plt
from lascar import AbstractContainer, Trace, Hdf5Container

# supress a lascar warning
# h5py.get_config().default_file_mode = "w"

# create a logger
logger = logging.getLogger('synthesize')
if (logger.hasHandlers()):
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# loading settings from file
settingsFile = "./settings.json"
parser = argparse.ArgumentParser(description='TOFU')
parser.add_argument('-s', '--settings', type=str, help='path to settings.json', required=False)
namespace = parser.parse_args()
if namespace.settings is not None:
    settingsFile = namespace.settings
settings = None
logger.info("loading settings from file: %s" % (settingsFile))
with open(settingsFile) as fid:
    settings = json.load(fid)


class synthesizeException(Exception):
    pass


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDifferenceFromBitString(x, y):
    return abs(hammingWeightFromBitString(x) - hammingWeightFromBitString(y))


# extracting signals from database
logger.info("extracting signals from signal properties")
signalPropertiesFile = settings["parse"]["signalPropertiesFile"]
signal_properties = []
with open(signalPropertiesFile, 'rb') as f:
    signal_properties = pickle.load(f)

signals = []
for signal in signal_properties:
    # signals.append({"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]})
    signals.append(int(signal[0]))

# reduce signals to distinct ones
signals = list(set(signals))

# extract signals which shoul be used for synthesis
signals_under_inspection = []
configFile = settings["synthesize"]["signalsFileName"]
if not os.path.isfile(configFile):
    logger.info("no signals configured generating standard signals.json")
    with open(configFile, "w", encoding="utf-8") as fid:
        json.dump(signals, fid, ensure_ascii=False, indent=4)
        signals_under_inspection = signals
else:
    logger.info("%s found using signals as specified" % (configFile))
    with open(configFile, "r", encoding="utf-8") as fid:
        signals_under_inspection = json.load(fid)


# extract the numeric ids under inspection
# numeric_ids_under_inspection = [i["numeric_id"] for i in signals_under_inspection]
numeric_ids_under_inspection = signals_under_inspection
# ids can appear in several scopes so reduce them
numeric_ids_under_inspection = list(set(numeric_ids_under_inspection))


# sort naturaly not in aphabetic order
def natural_sort_key(s):
    natural_sort_regex = re.compile('([0-9]+)')
    return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]


# globbing for pickle files
pickleFiles = glob.glob(settings["synthesize"]["pickleGlob"])
pickleFiles = sorted(pickleFiles, key=natural_sort_key)

# extract the number of traces
simulation_trace_max = len(pickleFiles)
logger.info("processing: %d traces" % (simulation_trace_max))


# Then the AbstractContainer:
class AcquisitionSetupToggle(AbstractContainer):
    def __init__(self,
                 pickleGlob,
                 signalPropertiesFile,
                 valueExtract,
                 numeric_ids_under_inspection=None,
                 reload_numeric_ids=False,
                 leakage="HammingDistance",
                 window=False,
                 windowFrom=None,
                 windowTo=None):
        """
        :param number_of_traces: only required argument for the constructor of an AbstractContainer
        """

        # extract the key
        # value extract function
        self.valueExtract = valueExtract

        # store the assumed leakage model
        self.leakage = leakage
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            pass
        # elif self.leakage == "HammingHybrid":
        #     pass
        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)

        self.window = window
        self.windowFrom = windowFrom
        self.windowTo = windowTo

        # signals which should be inspected
        self.numeric_ids_under_inspection = numeric_ids_under_inspection
        self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)

        self.reload_numeric_ids = reload_numeric_ids

        # extract signal properties
        self.signalPropertiesFile = signalPropertiesFile
        with open(self.signalPropertiesFile, 'rb') as f:
            self.signal_properties = pickle.load(f)
        self.signal_properties = [{"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]} for signal in self.signal_properties]

        signals = [i["numeric_id"] for i in self.signal_properties]
        signals = set(signals)
        # reduce signals to distinct ones
        logger.info("traces consist from %d signals" % (len(signals)))

        # sort naturaly not in aphabetic order
        def natural_sort_key(s):
            natural_sort_regex = re.compile('([0-9]+)')
            return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]

        # globbing for pickle files
        self.pickleGlob = pickleGlob
        self.pickleFiles = glob.glob(self.pickleGlob)
        self.pickleFiles = sorted(pickleFiles, key=natural_sort_key)

        self.number_of_traces = len(self.pickleFiles)

        # extract the simulation time stamps
        with open(self.pickleFiles[0], 'rb') as f:
            self.simulation_time_steps = pickle.load(f)
        self.simulation_time_steps = list(set([i[0] for i in self.simulation_time_steps]))
        self.simulation_time_steps.sort()
        self.simulation_time_to_index = {i[1]: i[0] for i in enumerate(self.simulation_time_steps)}
        self.simulation_index_to_time = {i[0]: i[1] for i in enumerate(self.simulation_time_steps)}
        self.simulation_time_max = self.simulation_time_steps[-1]
        logger.info("traces consist from %d sample points in time" % (len(self.simulation_time_steps)))

        AbstractContainer.__init__(self, self.number_of_traces)

    def generate_trace(self, index):
        """
        generate_trace is the only method needed by AcquisitionSetup to work properly
        :param index: index of trace, not used here.
        :return:  Trace with leakage from oscilloscope, and value from the dut plaintext/ciphertext
        """

        self.index = index

        time_start = time.time()
        self.logger.info("capturing trace: %d" % (index))

        if self.reload_numeric_ids:
            self.logger.info("reloading numeric ids")
            with open(configFile, "r", encoding="utf-8") as fid:
                self.numeric_ids_under_inspection = json.load(fid)
                self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)

        # horizontal mode assemmble state from changes and derive leakage
        # fetch all updates
        logger.info("extracting state updates from picklefile")
        self.updates = None
        with open(self.pickleFiles[index], 'rb') as f:
            self.updates = pickle.load(f)

        # extract key from pickle
        value = self.valueExtract(self)

        ###################################################################################################################################
        # slow slow slow remap this to something performant
        ###################################################################################################################################
        # input  : self.updates                               type: list of tuples
        # input  : self.simulation_time_to_index              type: dictonary int to int mapping
        # input  : self.windowFrom                            type: integer
        # input  : self.windowTo                              tpye: integer
        # input  : self.numeric_ids_under_inspection_set      type: set of integer
        # output : leakage                                    type: list of integers

        # extract the leakage
        leakage = np.zeros((len(self.simulation_time_steps),), dtype=np.int)

        # umbauen ummappen auf signale die benutzt werden
        state = np.zeros((len(self.signal_properties),), dtype=np.int)

        logger.info("iterating through all state updates")
        logger.info("performing %d updates" % (len(self.updates)))

        nextval_index_old = -1
        for update in self.updates:

            nextval_index = self.simulation_time_to_index[update[0]]

            # avoid the sum computation at all that thing slows down everything
            if self.window is True:
                if self.windowFrom is not None or self.windowTo is not None:
                    if nextval_index < self.windowFrom or nextval_index > self.windowTo:
                        nextval_index_old = nextval_index
                        continue

            numeric_id = update[1]

            # das bremst aus wie noch was
            # check if signal is tracked
            if numeric_id not in self.numeric_ids_under_inspection_set:
                continue

            nextval = hammingWeightFromBitString(update[2])

            logger.debug("simulation_time: %d index: %d  numeric_id: %d nextval: %d" % (update[0], nextval_index, numeric_id, nextval))
            if nextval_index != nextval_index_old:
                leakage[nextval_index_old:nextval_index + 1] = np.sum(state)
                nextval_index_old = nextval_index

            state[numeric_id] = nextval

        # last update after loop
        leakage[nextval_index_old:nextval_index + 1] = np.sum(state)

        ###################################################################################################################################

        # rolling mean using convolution
        # N = 5
        # leakage = np.convolve(leakage, np.ones((N,)) / N, mode='valid')

        # this extracts the hamming weight
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            # calculate the hamming distance
            shift_leakage = np.roll(leakage, 1)
            leakage = np.abs(leakage[1:] - shift_leakage[1:])
        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)

        if self.windowFrom is not None or self.windowTo is not None:
            logger.info("extracting window from leakage %d:%d" % (self.windowFrom, self.windowTo))
            leakage = leakage[self.windowFrom:self.windowTo]

        # dynamic scaling of trace eigentlich sollte man hier nach dem max suchen wenn das kleiner als max wer uint8 alles zu einem uint8

        # artifical noise
        # leakage += np.random.choice([0, 1], size=leakage.shape)

        time_finish = time.time()
        logger.info("capturing trace took %f seconds" % (time_finish - time_start))

        return Trace(leakage, value)


# if everything fits into ram use fastmode
pickleGlob = settings["synthesize"]["pickleGlob"]
signalPropertiesFile = settings["synthesize"]["signalPropertiesFile"]
leakageModel = settings["synthesize"]["leakageModel"]
traceFileName = settings["synthesize"]["traceFileName"]

# put null in json to load everything
window = settings["synthesize"]["window"]
windowFrom = settings["synthesize"]["windowFrom"]
windowTo = settings["synthesize"]["windowTo"]

writeTraces = settings["synthesize"]["writeTraces"]
writeTracesBatchSize = settings["synthesize"]["writeTracesBatchSize"]


valueExtractFunction = getattr(value, settings["synthesize"]["valueExtractFunction"])

# create our acquisition setup
aqc = AcquisitionSetupToggle(pickleGlob,
                             signalPropertiesFile,
                             valueExtractFunction,
                             numeric_ids_under_inspection,
                             leakage=leakageModel,
                             window=window,
                             windowFrom=windowFrom,
                             windowTo=windowTo,
                             reload_numeric_ids=True)

# export traces to container
if writeTraces:
    hdf5_container = Hdf5Container.export(aqc, traceFileName, batch_size=writeTracesBatchSize)

# print("trace 0:", aqc[0])
# print("trace 10:", aqc[10])

# so kann man plotten
# plt.plot(aqc[0][0])
# plt.show()

# verwendung mit externem tool
# aqc.generate_trace(1)


logger.info("synthesize traces from pickles finished")
