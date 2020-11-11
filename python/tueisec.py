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

class tueisecException(Exception):
    pass


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
        "dim": container.leakages.shape[1],
        "create": True
    }}
    # Initialize the HDF5 file
    h5filehandle = h5utils.hdf5_file_init(config, target_info="VCD dump simulation by TOFU tool.")
    N_traces = container.leakages.shape[0]
    # create group
    h5utils.hdf5_add_group(h5filehandle, config, N_traces=N_traces, noSamples=container.leakages.shape[1])

    # add traces (could also be done by h5utils.hdf5_add_data_multitrace?!)
    for trace_idx in range(0, N_traces):
        h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=container[trace_idx][0], trace_number=trace_idx, group=0)

    # close HDF5 file
    h5utils.hdf5_file_close(h5filehandle)