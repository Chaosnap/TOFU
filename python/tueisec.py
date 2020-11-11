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


class tueisecException(Exception):
    pass


def convert_time_scale(timescale_string):
    """
    Takes an input string of form '123ns', separates numbers and digits and converts the unit into factor of form 1e-9.
    :param timescale_string: input string of form '123ns'
    :return: timescale: float
    :return: timefactor: float
    """
    timescale = [re.findall(r'(\d+?)(\w+)', timescale_string)[0]][0]
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


def export(container, settings):
    try:
        from attack.helper.utils import JSONutils as jsonutils
        from attack.helper.utils import HDF5utils as h5utils
    except ImportError:
        raise tueisecException("Attack Framework not installed")

    # Use the file name specified by the settings file
    config = {"HDF5": {"output_file": settings["synthesize"]["traceFileName"]}}
    # create a dataset according the size and datatype of leakages
    config["HDF5"]['datasets'] = {"samples": {
        "datatype": container.leakages.dtype,
        "dim": None,
        "create": True
    }}
    num_samples = container.leakages.shape[1]
    try:
        # load the VCD metadata
        with open(container.signalPropertiesFile.rsplit('.', 1)[0] + '_meta.pickle', 'rb') as f:
            vcd_meta = pickle.load(f)

        timescale, timefactor = convert_time_scale(vcd_meta["timescale"])

        config["scope"] = {"sampling": {
            "sampling rate [S/s]": 1 / (timescale * timefactor),
            "sampling duration [s]": (container.simulation_time_steps[-1] - container.simulation_time_steps[-2]) * (
                    len(container.simulation_time_steps) - 1) * timefactor
        },
            "type": vcd_meta["version"],
            "channel1": {},
            "trigger": {}}
    except FileNotFoundError:
        pass

    # Initialize the HDF5 file
    h5filehandle = h5utils.hdf5_file_init(config, target_info="VCD dump simulation by TOFU tool.")
    n_traces = container.leakages.shape[0]
    # create group
    h5utils.hdf5_add_group(h5filehandle, config, N_traces=n_traces, noSamples=num_samples)

    # add traces (could also be done by h5utils.hdf5_add_data_multitrace?!)
    for trace_idx in range(0, n_traces):
        h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=container[trace_idx][0],
                              trace_number=trace_idx, group=0)

    # close HDF5 file
    h5utils.hdf5_file_close(h5filehandle)
