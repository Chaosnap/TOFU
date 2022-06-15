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
# Written by the following authors: Lars Tebelmann, Michael Gruber

import pickle
import re
import os
import numpy as np
import logging


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
    config["HDF5"]["datasets"] = {"samples": {"datatype": np.uint32, "dim": None, "create": True}}
    first_trace = container[0]
    num_samples = first_trace[0].shape[0]
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

    # save additional files in the __documentation__ entry of the HDF5 file
    try:
        # Add the desired files
        config["HDF5"]["documentation"] = settings["tueisecDocumentationFiles"]
        # Add the setting file
        config["HDF5"]["documentation"][settingsFileName] = settingsFileLocation
    except KeyError:
        # if the entry "tueisecDocumentationFiles" does not exist in the settings file, store only the settings file
        config["HDF5"]["documentation"] = {settingsFileName: settingsFileLocation}

    # convert relative paths to absolute paths (to ensure that relative paths are relative to the settings file)
    for key in config["HDF5"]["documentation"]:
        if not os.path.isabs(config["HDF5"]["documentation"][key]):
            config["HDF5"]["documentation"][key] = settingsFilePath + config["HDF5"]["documentation"][key]

    # Initialize the HDF5 file
    h5filehandle = h5utils.hdf5_file_init(config, target_info="VCD dump simulation by TOFU tool.")
    n_traces = len(container)
    # create group
    h5utils.hdf5_add_group(h5filehandle, config, N_traces=n_traces, noSamples=num_samples)

    # specify additional datasets, e.g. with input, output and secret data/key
    try:
        # if specified in the settings file, use datasetnames and files specified
        file_dict = settings["tueisecAdditionalDataSets"]
        datasetname = list(file_dict.keys())
        npyfiles = list(file_dict.values())
    except KeyError:
        # if entry does not exist in settingss, find all .npy files in the same folder as the .vcd files and add the data contained as datasets to the HDF5
        vcd_dump_path = settings["pickleGlob"]
        if not os.path.isabs(settings["pickleGlob"]):
            vcd_dump_path = settingsFilePath + vcd_dump_path
        vcddir = os.path.dirname(vcd_dump_path) + "/"  # same folder as VCD files
        npyfiles = [vcddir + f for f in os.listdir(vcddir) if f.endswith(".npy")]  # get list of .npy files
        datasetname = [os.path.splitext(os.path.split(f)[1])[0] for f in npyfiles]  # use the filename of .npy files for the dataset name in the hdf5

    # convert relative paths to absolute paths (to ensure that relative paths are relative to the settings file)
    for fdx, f in enumerate(npyfiles):
        if not os.path.isabs(f):
            npyfiles[fdx] = settingsFilePath + npyfiles[fdx]

    # save additional datasets in HDF5
    for file, dataset in zip(npyfiles, datasetname):
        # directly copy data. Requires the user to take care that the correct data is present
        data = np.atleast_3d(np.load(file, "r"))
        h5filehandle["0000"][dataset] = data
        if data.shape[0] != n_traces:
            logging.warning("The file %s contains data for %i trace, but %i are simulated." % (file, data.shape[0], n_traces))

    # add traces (could also be done by h5utils.hdf5_add_data_multitrace?!)
    for trace_idx in range(0, n_traces):
        # avoid synthesizing the first trace again
        if trace_idx == 0:
            data = first_trace[0]
        else:
            data = container[trace_idx][0]
        h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=data, trace_number=trace_idx, group=0)

    # close HDF5 file
    h5utils.hdf5_file_close(h5filehandle)
