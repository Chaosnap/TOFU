#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: analyze.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import logging
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from lascar import Hdf5Container, TTestEngine, MatPlotLibOutputMethod, Session
import random

# supress a lascar warning
h5py.get_config().default_file_mode = "r+"


# create a logger
logger = logging.getLogger('analyze')
if (logger.hasHandlers()):
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

# loading settings from file
settings = None
settingsFile = "./settings.json"
logger.info("loading settings from file: %s" % (settingsFile))
with open("./settings.json") as fid:
    settings = json.load(fid)


logger.info("starting analysis")


traceFileName = settings["synthesize"]["traceFileName"]
container = Hdf5Container(traceFileName)

fixedVal = settings["analyze"]["value_signal_fixed"]


def partition_function(value):
    # partition_function must take 1 argument: the value returned by the container at each trace
    compare = ([value][0] == np.array(fixedVal, dtype=np.uint8)).all()
    logger.debug("compare with fixed value: %r" % (compare))
    # return random.randint(0, 1)
    return compare


def _foo_finalize(self):
    # ???
    m0 = self._acc_x_by_partition[0, 0] / self._partition_count[0]
    m1 = self._acc_x_by_partition[0, 1] / self._partition_count[1]

    logger.debug("m0: %s" % m0)
    logger.debug("m1: %s" % m1)

    v0 = (self._acc_x_by_partition[1, 0] / self._partition_count[0]) - m0 ** 2
    v1 = (self._acc_x_by_partition[1, 1] / self._partition_count[1]) - m1 ** 2

    logger.debug("v0: %s" % v0)
    logger.debug("v1: %s" % v1)
    logger.debug("m0-m1: %s" % (m0 - m1))

    # how to catch that
    with np.errstate(divide='ignore', invalid='ignore'):
        result = (m0 - m1) / (np.sqrt((v0 / self._partition_count[0]) + (v1 / self._partition_count[1])))
        logger.debug("result: %s" % result)
        result = np.nan_to_num(result, copy=False, nan=0.0, posinf=100, neginf=100)
        logger.debug("result: %s" % result)
    return result


TTestEngine._finalize = _foo_finalize
ttest_engine = TTestEngine("ttest", partition_function)


plot_output = MatPlotLibOutputMethod(ttest_engine)

session = Session(container, output_method=plot_output)
session.add_engine(ttest_engine)
# session.run(batch_size=2500)
session.run()


logger.info("analysis finished")
