#!/usr/bin/python3
import logging
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from lascar import Hdf5Container, TTestEngine, MatPlotLibOutputMethod, Session

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
    return False


ttest_engine = TTestEngine("ttest", partition_function)


plot_output = MatPlotLibOutputMethod(ttest_engine)

session = Session(container, output_method=plot_output)
session.add_engine(ttest_engine)
session.run(batch_size=2500)


logger.info("analysis finished")
