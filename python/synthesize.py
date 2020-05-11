#!/usr/bin/python3
import logging
import sqlite3
import json
import os.path
import numpy as np
from lascar import AbstractContainer, Trace, Hdf5Container

import matplotlib.pyplot as plt

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
fileNameDatabase = "./traces.db"
conn = sqlite3.connect(fileNameDatabase)
cursor = conn.cursor()


# extracting signals from database
logger.info("extracting signals from database")
EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT name, width, scope FROM signals"
signals = {}
for signal in cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY):
    signals[signal[0]] = {"width": int(signal[1]), "scope": signal[2]}


# extract signals which shoul be used for synthesis
signals_under_inspection = []
configFile = "./signals.json"
if not os.path.isfile(configFile):
    logger.info("no signals configured generating standard signals.json")
    with open(configFile, "w", encoding="utf-8") as fid:
        json.dump(list(signals.keys()), fid, ensure_ascii=False, indent=4)
        signals_under_inspection = list(signals.keys())
else:
    logger.info("signals.json found using signals as specified")
    with open(configFile, "r", encoding="utf-8") as fid:
        signals_under_inspection = json.load(fid)

# extract the number of traces
SIMULATION_TRACES_QUERY = 'SELECT max(simulation_trace) from traces'
cursor.execute(SIMULATION_TRACES_QUERY)
simulation_trace_max = cursor.fetchone()[0]
logger.info("processing: %d traces" % (simulation_trace_max + 1))


# extract the simulation time stamps
# SIMULATION_TIME_STEPS_QUERY = 'SELECT DISTINCT simulation_time from traces ORDER BY simulation_time ASC'
# cursor.execute(SIMULATION_TIME_STEPS_QUERY)
# simulation_time_steps = cursor.fetchall()
# simulation_time_steps = [i[0] for i in simulation_time_steps]
# simulation_time_max = simulation_time_steps[-1]
# logger.info("traces consist from %d sample points in time" % (len(simulation_time_steps)))

# # extract the signals
# SIGNAL_VALUE_QUERY = 'SELECT %s from traces WHERE simulation_time=? AND simulation_trace=?' % \
#     (", ".join(["\"" + i + "\"" for i in list(signals.keys())]))
# cursor.execute(SIGNAL_VALUE_QUERY, (0, 0))
# blah = cursor.fetchone()
# hammingWeightState = None
# hammingWeightState_old = hammingWeightState
# hammingWeightState = sum([hammingWeightFromBitString(i) for i in list(blah)])

conn.commit()
conn.close()


# Then the AbstractContainer:
class AcquisitionSetupToggle(AbstractContainer):
    def __init__(self, number_of_traces, database, signals_under_inspection, leakage="HammingDistance"):
        """
        :param number_of_traces: only required argument for the constructor of an AbstractContainer
        """
        # create database connection
        self.database = database
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()

        # store the assumed leakage model
        self.leakage = leakage
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            pass
        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)

        # signals which should be inspected
        self.signals_under_inspection = signals_under_inspection

        # extract signal properties
        self.signal_properties = {}
        EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT name, width, scope FROM signals"
        signals = {}
        for signal in self.cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY):
            self.signal_properties[signal[0]] = {"width": int(signal[1]), "scope": signal[2]}

        # extract the simulation time stamps
        SIMULATION_TIME_STEPS_QUERY = 'SELECT DISTINCT simulation_time from traces ORDER BY simulation_time ASC'
        self.cursor.execute(SIMULATION_TIME_STEPS_QUERY)
        self.simulation_time_steps = self.cursor.fetchall()
        self.simulation_time_steps = [i[0] for i in self.simulation_time_steps]
        self.simulation_time_max = self.simulation_time_steps[-1]
        logger.info("traces consist from %d sample points in time" % (len(self.simulation_time_steps)))

        AbstractContainer.__init__(self, number_of_traces)

    def generate_trace(self, index):
        """
        generate_trace is the only method needed by AcquisitionSetup to work properly
        :param index: index of trace, not used here.
        :return:  Trace with leakage from oscilloscope, and value from the dut plaintext/ciphertext
        """

        self.logger.info("capturing trace: %d" % (index))

        # extract the key
        # ANPASSEN !!!
        value_signal = 'key [15:0]'
        value_signal_time = 80000
        KEY_VALUE_QUERY = 'SELECT \"%s\" from traces WHERE simulation_time=? AND simulation_trace=?' % value_signal
        self.cursor.execute(KEY_VALUE_QUERY, (value_signal_time, index))
        value = self.cursor.fetchone()[0]
        value_width = self.signal_properties['clk']['width']

        if not value_width % 8:
            raise synthesizeException("value width must be multiple of byte: %d" % value_width)

        value = value.zfill(value_width)
        value = bytearray(int(value, 2).to_bytes((len(value) + 7) // 8, 'big'))
        value = np.array([value], dtype=np.uint8)

        # extract the leakage
        leakage = np.zeros((len(self.simulation_time_steps),), dtype=int)

        # das sollte auch schneller gehen wenn man alles fetcht und dann zusammen baut

        # this extracts the hamming weight
        if self.leakage == "HammingWeight":
            for (timeindex, simulation_time) in enumerate(self.simulation_time_steps):
                SIGNAL_VALUE_QUERY = 'SELECT %s from traces WHERE simulation_time=? AND simulation_trace=?' % \
                    (", ".join(["\"" + i + "\"" for i in self.signals_under_inspection]))
                self.cursor.execute(SIGNAL_VALUE_QUERY, (simulation_time, index))
                blah = self.cursor.fetchone()
                leakage[timeindex] = sum([hammingWeightFromBitString(i) for i in list(blah)])

        # this extracts the hamming distance
        elif self.leakage == "HammingDistance":
            lastHammingWeightState = 0
            for (timeindex, simulation_time) in enumerate(self.simulation_time_steps):
                SIGNAL_VALUE_QUERY = 'SELECT %s from traces WHERE simulation_time=? AND simulation_trace=?' % \
                    (", ".join(["\"" + i + "\"" for i in self.signals_under_inspection]))
                self.cursor.execute(SIGNAL_VALUE_QUERY, (simulation_time, index))
                blah = self.cursor.fetchone()
                hammingWeightState = sum([hammingWeightFromBitString(i) for i in list(blah)])
                leakage[timeindex] = abs(hammingWeightState - lastHammingWeightState)
                lastHammingWeightState = hammingWeightState

        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)
        return Trace(leakage, value)


# aqc = AcquisitionSetupToggle(simulation_trace_max + 1, fileNameDatabase, signals_under_inspection, leakage="HammingWeight")
aqc = AcquisitionSetupToggle(simulation_trace_max + 1, fileNameDatabase, signals_under_inspection, leakage="HammingDistance")

# hdf5_container = Hdf5Container.export(aqc, "traces.h5")

# print("trace 0:", aqc[0])
# print("trace 10:", aqc[10])

# so kann man plotten
# plt.plot(aqc[0][0])
# plt.show()


logger.info("synthesize traces from database finished")
