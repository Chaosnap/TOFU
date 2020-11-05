#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: lascar_to_tueisec.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

from attack.helper.utils import JSONutils as jsonutils
from attack.helper.utils import HDF5utils as h5utils
import argparse
import logging
import json
import time
import numpy as np
import h5py
import matplotlib.pyplot as plt
from lascar import Hdf5Container


# supress a lascar warning
h5py.get_config().default_file_mode = "r+"

# work with huge plots
plt.rcParams['agg.path.chunksize'] = 10000

# create a logger
logger = logging.getLogger('convert')
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


logger.info("starting conversion")


container = Hdf5Container(settings["synthesize"]["traceFileName"])
traceFileName = "tueisec_" + settings["synthesize"]["traceFileName"]


# Use the file name specified by the settings file
config = {"HDF5": {"output_file": "foo.h5"}}
# create a dataset according the size and datatype of leakages
config["HDF5"]['datasets'] = {"samples": {
    "datatype": container.leakages.dtype,
    "dim": container.leakages.shape[1],
    "create": True
}}
# Initialize the HDF5 file
h5filehandle = h5utils.hdf5_file_init(config, target_info="VCD dump simulation by TOFU tool.")
# TODO: educated guess that container.leakages.shape[0] is the number of traces if more than one exists

h5utils.hdf5_add_group(h5filehandle, config, N_traces=container.leakages.shape[0], noSamples=container.leakages.shape[1])

h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=container[0][0], trace_number=0, group=0)
# close HDF5 file
h5filehandle = h5utils.hdf5_file_close(h5filehandle)
