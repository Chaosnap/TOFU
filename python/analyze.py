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

import argparse
import logging
import json
import time
import numpy as np
import h5py
import matplotlib.pyplot as plt
from lascar import Hdf5Container, TTestEngine, MatPlotLibOutputMethod, Hdf5OutputMethod, Session
import random

# supress a lascar warning
h5py.get_config().default_file_mode = "r+"

# work with huge plots
plt.rcParams['agg.path.chunksize'] = 10000

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


logger.info("starting analysis")


traceFileName = settings["analyze"]["traceFileName"]
container = Hdf5Container(traceFileName)

fixedVal = settings["analyze"]["value_signal_fixed"]


def partition_function(value):
    # partition_function must take 1 argument: the value returned by the container at each trace
    compare = ([value][0] == np.array(fixedVal, dtype=np.uint8)).all()
    logger.debug("compare with fixed value: %r" % (compare))
    # return random.randint(0, 1)
    return compare


def _foo_finalize(self):

    # size
    n0 = self._partition_count[0]
    n1 = self._partition_count[1]

    # mean
    m0 = self._acc_x_by_partition[0, 0] / self._partition_count[0]
    m1 = self._acc_x_by_partition[0, 1] / self._partition_count[1]

    # variance
    v0 = (self._acc_x_by_partition[1, 0] / self._partition_count[0]) - m0 ** 2
    v1 = (self._acc_x_by_partition[1, 1] / self._partition_count[1]) - m1 ** 2

    logger.debug("n0: %d" % (n0))
    logger.debug("n1: %d" % (n1))

    logger.debug("m0: %s" % m0)
    logger.debug("m1: %s" % m1)

    logger.debug("v0: %s" % v0)
    logger.debug("v1: %s" % v1)

    # how to catch that
    with np.errstate(divide='ignore', invalid='ignore'):
        result = (m0 - m1) / (np.sqrt((v0 / n0) + (v1 / n1)))
        logger.debug("result: %s" % result)
        # result = np.nan_to_num(result, copy=False, nan=10, posinf=10, neginf=10)
        # since we have no noise set the vals to zero
        result = np.nan_to_num(result, copy=False, nan=0, posinf=0, neginf=0)

    return result


time_start = time.time()

TTestEngine._finalize = _foo_finalize
ttest_engine = TTestEngine("ttest", partition_function)


# plot mix max t value
plt.axhline(y=+4.5, color='r', linestyle='-')
plt.axhline(y=-4.5, color='r', linestyle='-')

# gimli
plt.axvline(x=1358530, color='g', linestyle='-')
plt.axvline(x=1360770, color='g', linestyle='-')

# key loading
plt.axvline(x=1358670, color='g', linestyle='-')
plt.axvline(x=1358703, color='g', linestyle='-')

# tag
plt.axvline(x=1360500, color='g', linestyle='-')
plt.axvline(x=1360700, color='g', linestyle='-')


# plt.axvline(x=32455, color='g', linestyle='-')
# plt.axvline(x=32653, color='g', linestyle='-')
# plt.axvline(x=32645, color='y', linestyle='-')
# plt.axvline(x=32662, color='y', linestyle='-')


plot_output = MatPlotLibOutputMethod(ttest_engine)
session = Session(container, output_method=plot_output)
session.add_engine(ttest_engine)
# session.run(batch_size=2500)
session.run()


# hdf5_output = Hdf5OutputMethod("foo.h5", ttest_engine)
# session = Session(container, output_method=hdf5_output)
# session.add_engine(ttest_engine)
# # session.run(batch_size=2500)
# session.run()


time_finish = time.time()
logger.info("analysis finished took %f seconds" % (time_finish - time_start))
