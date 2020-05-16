#!/usr/bin/python3
import logging
import sqlite3
import json
import os.path
import numpy as np
import h5py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# create a logger
logger = logging.getLogger('visualize')
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
settings = None
settingsFile = "./settings.json"
logger.info("loading settings from file: %s" % (settingsFile))
with open("./settings.json") as fid:
    settings = json.load(fid)


class visualizeException(Exception):
    pass


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDifferenceFromBitString(x, y):
    return abs(hammingWeightFromBitString(x) - hammingWeightFromBitString(y))


# create database connection
logger.info("connecting to database")
fileNameDatabase = settings["visualize"]["database"]
conn = sqlite3.connect(fileNameDatabase)
cursor = conn.cursor()


# extracting signals from database
logger.info("extracting signals from database")
EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT numeric_id, name, width, scope FROM signals"
signals = []
for signal in cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY):
    # signals.append({"numeric_id": int(signal[0]), "name": signal[1], "width": int(signal[2]), "scope": signal[3]})
    signals.append(int(signal[0]))

# reduce signals to distinct ones
signals = list(set(signals))

# extract signals which shoul be used for synthesis
signals_under_inspection = []
configFile = settings["visualize"]["signalsFileName"]
if not os.path.isfile(configFile):
    logger.info("no signals configured generating standard signals.json")
    with open(configFile, "w", encoding="utf-8") as fid:
        json.dump(signals, fid, ensure_ascii=False, indent=4)
        signals_under_inspection = signals
else:
    logger.info("%s found using signals as specified" % (configFile))
    with open(configFile, "r", encoding="utf-8") as fid:
        signals_under_inspection = json.load(fid)


# extract the numeric ids under inspection
# numeric_ids_under_inspection = [i["numeric_id"] for i in signals_under_inspection]
numeric_ids_under_inspection = signals_under_inspection
# ids can appear in several scopes so reduce them
numeric_ids_under_inspection = list(set(numeric_ids_under_inspection))


# extract the number of traces
SIMULATION_TRACES_QUERY = 'SELECT max(simulation_trace) from traces'
cursor.execute(SIMULATION_TRACES_QUERY)
simulation_trace_max = cursor.fetchone()[0]
logger.info("processing: %d traces" % (simulation_trace_max + 1))


plotsFileName = settings["visualize"]["plotsFileName"]

# signals which should be inspected
numeric_ids_under_inspection = numeric_ids_under_inspection
numeric_ids_under_inspection_set = set(numeric_ids_under_inspection)

# extract signal properties
EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT DISTINCT numeric_id, width FROM signals ORDER BY numeric_id ASC"
cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY)
signal_properties = cursor.fetchall()
signal_properties = [{"numeric_id": int(signal[0]), "width": int(signal[1])} for signal in signal_properties]
logger.info("traces consist from %d signals" % (len(signal_properties)))

# extract the simulation time stamps
SIMULATION_TIME_STEPS_QUERY = 'SELECT DISTINCT simulation_time from traces ORDER BY simulation_time ASC'
cursor.execute(SIMULATION_TIME_STEPS_QUERY)
simulation_time_steps = cursor.fetchall()
simulation_time_steps = [i[0] for i in simulation_time_steps]
simulation_time_to_index = {i[1]: i[0] for i in enumerate(simulation_time_steps)}
simulation_index_to_time = {i[0]: i[1] for i in enumerate(simulation_time_steps)}
simulation_time_max = simulation_time_steps[-1]
logger.info("traces consist from %d sample points in time" % (len(simulation_time_steps)))


# extract the leakage
leakage = np.zeros((len(simulation_time_steps),), dtype=np.int)


simulationTrace = settings["visualize"]["simulationTrace"]


# vertical approach assemble leakage over the signals
with PdfPages(plotsFileName) as pdf:
    for numeric_id in numeric_ids_under_inspection:

        plt.figure()
        plt.title("compsed up to signal %d" % numeric_id)

        signal_leakage = np.zeros((len(simulation_time_steps),), dtype=np.int)

        logger.info("processing signal with numeric id: %d" % (numeric_id))

        SIGNAL_UPDATE_QUERY = 'SELECT simulation_time, nextval from traces WHERE simulation_trace=? AND numeric_id=?  ORDER BY simulation_time ASC'
        nextval_index_old = -1
        nextval_val_old = 0
        for update in cursor.execute(SIGNAL_UPDATE_QUERY, (simulationTrace, numeric_id)):
            logger.debug("%s" % (simulation_time_to_index[update[0]]))
            nextval_index = simulation_time_to_index[update[0]]
            nextval_val = hammingWeightFromBitString(update[1])
            signal_leakage[nextval_index_old:nextval_index + 1] = nextval_val_old
            nextval_index_old = nextval_index
            nextval_val_old = nextval_val

        signal_leakage[nextval_index_old:] = nextval_val_old
        leakage += signal_leakage

        plt.plot(leakage)
        plt.grid()
        pdf.savefig()
        plt.close()


conn.commit()
conn.close()


logger.info("visualize traces from database finished")
