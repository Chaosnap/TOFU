#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: tueisec.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import pickle
import re
import os
import numpy as np


class tueisecException(Exception):
    pass


def convert_time_scale(timescale_string):
    """
    Takes an input string of form '123ns', separates numbers and digits and converts the unit into factor of form 1e-9.
    :param timescale_string: input string of form '123ns'
    :return: timescale: float
    :return: timefactor: float
    """
    timescale = [re.findall(r"(\d+?)(\w+)", timescale_string)[0]][0]
    if timescale[1] == "ps":
        timefactor = 1e-12
    elif timescale[1] == "ns":
        timefactor = 1e-9
    elif timescale[1] == "us":
        timefactor = 1e-6
    elif timescale[1] == "ms":
        timefactor = 1e-3
    else:
        timefactor = 1
    return float(timescale[0]), timefactor


def export(container, settings, settingsFileLocation="./"):
    """
    Export function to generate a HDF5 in the TUEISEC format from simulations
    :param container: container with the simulated traces
    :param settings: dictionary from the provided settings file
    :param settingsFileLocation: absolute path of the settings file (including filename)
    :return:
    """
    try:
        from attack.helper.utils import HDF5utils as h5utils
    except ImportError:
        raise tueisecException("Attack Framework not installed")

    # Get absolute file path and file name of the settings file
    settingsFilePath = os.path.dirname(settingsFileLocation) + "/"
    settingsFileName = os.path.split(settingsFileLocation)[1]

    # Use the file name specified by the settings file
    outputfilename = settings["traceFileName"]
    if not os.path.isabs(outputfilename):
        # If a relative path is given, join with the path where the settings file is located, i.e. paths are relative to the settings file
        outputfilename = settingsFilePath + outputfilename

    config = {"HDF5": {"output_file": outputfilename}}
    # create a dataset according the size and datatype of leakages
    config["HDF5"]["datasets"] = {"samples": {"datatype": container.leakages.dtype, "dim": None, "create": True}}
    num_samples = container.leakages.shape[1]
    try:
        # load the VCD metadata
        with open(container.signalPropertiesFile.rsplit(".", 1)[0] + "_meta.pickle", "rb") as f:
            vcd_meta = pickle.load(f)

        timescale, timefactor = convert_time_scale(vcd_meta["timescale"])

        config["scope"] = {
            "sampling": {"sampling rate [S/s]": 1 / (timescale * timefactor), "sampling duration [s]": (container.simulation_time_steps[-1] - container.simulation_time_steps[-2]) * (len(container.simulation_time_steps) - 1) * timefactor},
            "type": "Vivado " + vcd_meta["version"],
            "channel1": {},
            "trigger": {},
        }
    except FileNotFoundError:
        pass

    # Add the Leakage model
    config["scope"]["sampling"]["leakage model"] = container.leakage

    # save the settings file in the HDF5
    config["HDF5"]["documentation"] = {settingsFileName: settingsFileLocation}

    # Initialize the HDF5 file
    h5filehandle = h5utils.hdf5_file_init(config, target_info="VCD dump simulation by TOFU tool.")
    n_traces = container.leakages.shape[0]
    # create group
    h5utils.hdf5_add_group(h5filehandle, config, N_traces=n_traces, noSamples=num_samples)

    # find all .npy files in the same folder as the .vcd files and add the data contained as datasets to the HDF5
    vcd_dump_path = settings["pickleGlob"]
    if not os.path.isabs(settings["pickleGlob"]):
        vcd_dump_path = settingsFilePath + vcd_dump_path
    vcddir = os.path.dirname(vcd_dump_path) + "/"  # same folder as VCD files
    npyfiles = [f for f in os.listdir(vcddir) if f.endswith(".npy")]  # get list of .npy files
    for file in npyfiles:
        # use filename as dataset name
        datasetname = os.path.splitext(file)[0]
        # directly copy data. Requires the user to take care that the correct data is present
        h5filehandle["0000"][datasetname] = np.atleast_3d(np.load(vcddir + file, "r"))

    # add traces (could also be done by h5utils.hdf5_add_data_multitrace?!)
    for trace_idx in range(0, n_traces):
        h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=container[trace_idx][0], trace_number=trace_idx, group=0)

    # close HDF5 file
    h5utils.hdf5_file_close(h5filehandle)
