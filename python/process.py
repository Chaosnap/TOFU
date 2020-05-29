#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: process.py
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
import time
import matplotlib.pyplot as plt
from lascar import AbstractContainer, Trace, Hdf5Container

# supress a lascar warning
# h5py.get_config().default_file_mode = "w"

# create a logger
logger = logging.getLogger('process')
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


class processException(Exception):
    pass


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDifferenceFromBitString(x, y):
    return abs(hammingWeightFromBitString(x) - hammingWeightFromBitString(y))


# Then the AbstractContainer:
class AcquisitionSetupProcess(AbstractContainer):
    def __init__(self,
                 traceFileNameInput,
                 traceFileNameOutput,
                 leakage="HammingDistance",
                 rollingMean=False,
                 rollingMeanWindow=0,
                 window=False,
                 windowFrom=None,
                 windowTo=None):

        self.traceFileNameInput = traceFileNameInput
        self.traceFileNameOutput = traceFileNameOutput
        self.container = Hdf5Container(self.traceFileNameInput)

        self.rollingMean = rollingMean
        self.rollingMeanWindow = rollingMeanWindow

        # store the assumed leakage model
        self.leakage = leakage
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            pass
        # elif self.leakage == "HammingHybrid":
        #     pass
        else:
            raise processException("undefined leakage model: %s" % self.leakage)

        self.window = window
        self.windowFrom = windowFrom
        self.windowTo = windowTo

        self.number_of_traces = len(self.container)
        self.len_trace = len(self.container[0][0])

        logger.info("traces consist from %d sample points in time" % (self.len_trace))

        AbstractContainer.__init__(self, self.number_of_traces)

    def generate_trace(self, index):
        self.index = index
        time_start = time.time()
        self.logger.debug("capturing trace: %d" % (index))

        # extract leakage and value
        leakage = self.container[index][0]
        value = self.container[index][1]

        # rolling mean using convolution
        if self.rollingMean:
            N = self.rollingMeanWindow
            leakage = np.convolve(leakage, np.ones((N,)) / N, mode='valid')

        # this extracts the hamming weight
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            # calculate the hamming distance
            shift_leakage = np.roll(leakage, 1)
            leakage = np.abs(leakage[1:] - shift_leakage[1:])
        else:
            raise processException("undefined leakage model: %s" % self.leakage)

        if self.windowFrom is not None or self.windowTo is not None:
            if self.window is True:
                # logger.debug("extracting window from leakage %d:%d" % (self.windowFrom, self.windowTo))
                leakage = leakage[self.windowFrom:self.windowTo]

        # artifical noise
        # leakage += np.random.choice([0, 1], size=leakage.shape)

        time_finish = time.time()
        logger.debug("conversion of trace took %f seconds" % (time_finish - time_start))

        return Trace(leakage, value)


leakageModel = settings["process"]["leakageModel"]
traceFileNameInput = settings["process"]["traceFileNameInput"]
traceFileNameOutput = settings["process"]["traceFileNameOutput"]
writeTraces = settings["process"]["writeTraces"]
writeTracesBatchSize = settings["process"]["writeTracesBatchSize"]
rollingMean = settings["process"]["rollingMean"]
rollingMeanWindow = settings["process"]["rollingMeanWindow"]
window = settings["process"]["window"]
windowFrom = settings["process"]["windowFrom"]
windowTo = settings["process"]["windowTo"]

# create our acquisition setup
aqc = AcquisitionSetupProcess(traceFileNameInput,
                              traceFileNameOutput,
                              leakage=leakageModel,
                              rollingMean=rollingMean,
                              rollingMeanWindow=rollingMeanWindow,
                              window=window,
                              windowFrom=windowFrom,
                              windowTo=windowTo)

# export traces to container
if writeTraces:
    try:
        hdf5_container._file.close()
    except NameError:
        pass
    hdf5_container = Hdf5Container.export(aqc, traceFileNameOutput, batch_size=writeTracesBatchSize)

logger.info("process traces hamming trace finished")
