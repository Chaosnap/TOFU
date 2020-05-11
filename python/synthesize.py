#!/usr/bin/python3
import logging
import sqlite3
import json
import os.path
import lascar

# create a logger
logger = logging.getLogger('synthesize')
if (logger.hasHandlers()):
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)


class synthesizeException(Exception):
    pass


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDifferenceFromBitString(x, y):
    return abs(hammingWeightFromBitString(x) - hammingWeightFromBitString(y))


# create database connection
logger.info("connecting to database")
conn = sqlite3.connect("./traces.db")
cursor = conn.cursor()


# extracting signals from database
logger.info("extracting signals from database")
EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT name, width, scope FROM signals"
signals = {}
for signal in cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY):
    signals[signal[0]] = {"width": int(signal[1]), "scope": signal[2]}


# extract signals which shoul be used for synthesis
configFile = "./signals.json"
if not os.path.isfile(configFile):
    logger.info("no signals configured generating standard signals.json")
    with open(configFile, "w", encoding="utf-8") as fid:
        json.dump(list(signals.keys()), fid, ensure_ascii=False, indent=4)
else:
    logger.info("signals.json found using signals as specified")

# extract the number of traces
SIMULATION_TRACES_QUERY = 'SELECT max(simulation_trace) from traces'
cursor.execute(SIMULATION_TRACES_QUERY)
simulation_trace_max = cursor.fetchone()[0]
logger.info("processing: %d traces" % (simulation_trace_max + 1))


# extract the simulation time stamps
SIMULATION_TIME_STEPS_QUERY = 'SELECT DISTINCT simulation_time from traces ORDER BY simulation_time ASC'
cursor.execute(SIMULATION_TIME_STEPS_QUERY)
simulation_time_steps = cursor.fetchall()
simulation_time_steps = [i[0] for i in simulation_time_steps]
simulation_time_max = simulation_time_steps[-1]
logger.info("traces consist from %d sample points in time" % (len(simulation_time_steps)))

# extract the signals
SIGNAL_VALUE_QUERY = 'SELECT %s from traces WHERE simulation_time=? AND simulation_trace=?' % \
    (", ".join(["\"" + i + "\"" for i in list(signals.keys())]))
cursor.execute(SIGNAL_VALUE_QUERY, (0, 0))
blah = cursor.fetchone()


hammingWeightState = None
hammingWeightState_old = hammingWeightState
hammingWeightState = sum([hammingWeightFromBitString(i) for i in list(blah)])


# extrac partition value i.e. key

# iterate over all traces
# iterate over all time steps


conn.commit()
conn.close()
logger.info("synthesize traces from database finished")
