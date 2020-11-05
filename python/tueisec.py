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
    # TODO: educated guess that container.leakages.shape[0] is the number of traces if more than one exists

    h5utils.hdf5_add_group(h5filehandle, config, N_traces=container.leakages.shape[0], noSamples=container.leakages.shape[1])

    h5utils.hdf5_add_data(h5filehandle=h5filehandle, dataset_name="samples", data=container[0][0], trace_number=0, group=0)
    # close HDF5 file
    h5utils.hdf5_file_close(h5filehandle)
