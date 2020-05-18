#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: synthesize.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import logging
import sqlite3
import json
import os.path
import numpy as np
import h5py
import matplotlib.pyplot as plt
from lascar import AbstractContainer, Trace, Hdf5Container

# supress a lascar warning
h5py.get_config().default_file_mode = "w"

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
logger.setLevel(logging.INFO)

# loading settings from file
settings = None
settingsFile = "./settings.json"
logger.info("loading settings from file: %s" % (settingsFile))
with open("./settings.json") as fid:
    settings = json.load(fid)


class synthesizeException(Exception):
    pass


def hammingWeightFromBitString(x):
    return x.count("1")


def hammingDifferenceFromBitString(x, y):
    return abs(hammingWeightFromBitString(x) - hammingWeightFromBitString(y))


# create database connection
logger.info("connecting to database")
fileNameDatabase = settings["synthesize"]["database"]
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
configFile = settings["synthesize"]["signalsFileName"]
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
    def __init__(self,
                 number_of_traces,
                 database,
                 numeric_ids_under_inspection=None,
                 reload_numeric_ids=False,
                 leakage="HammingDistance",
                 windowFrom=None,
                 windowTo=None,
                 fastMode=False,
                 value_signal_numeric_id=None,
                 value_signal_time=None):
        """
        :param number_of_traces: only required argument for the constructor of an AbstractContainer
        """
        # create database connection
        self.database = database
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()

        self.fastMode = fastMode

        # extract the key
        # ANPASSEN !!!
        self.value_signal_numeric_id = value_signal_numeric_id
        self.value_signal_time = value_signal_time

        # store the assumed leakage model
        self.leakage = leakage
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            pass
        elif self.leakage == "HammingHybrid":
            pass
        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)

        self.windowFrom = windowFrom
        self.windowTo = windowTo

        # signals which should be inspected
        self.numeric_ids_under_inspection = numeric_ids_under_inspection
        self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)

        self.reload_numeric_ids = reload_numeric_ids

        # extract signal properties
        EXTRACT_SIGNAL_PROPERTY_QUERY = "SELECT DISTINCT numeric_id, width FROM signals ORDER BY numeric_id ASC"
        self.cursor.execute(EXTRACT_SIGNAL_PROPERTY_QUERY)
        self.signal_properties = self.cursor.fetchall()
        self.signal_properties = [{"numeric_id": int(signal[0]), "width": int(signal[1])} for signal in self.signal_properties]
        logger.info("traces consist from %d signals" % (len(self.signal_properties)))

        # extract the simulation time stamps
        SIMULATION_TIME_STEPS_QUERY = 'SELECT DISTINCT simulation_time from traces ORDER BY simulation_time ASC'
        self.cursor.execute(SIMULATION_TIME_STEPS_QUERY)
        self.simulation_time_steps = self.cursor.fetchall()
        self.simulation_time_steps = [i[0] for i in self.simulation_time_steps]
        self.simulation_time_to_index = {i[1]: i[0] for i in enumerate(self.simulation_time_steps)}
        self.simulation_index_to_time = {i[0]: i[1] for i in enumerate(self.simulation_time_steps)}
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

        if self.reload_numeric_ids:
            self.logger.info("reloading numeric ids")
            with open(configFile, "r", encoding="utf-8") as fid:
                self.numeric_ids_under_inspection = json.load(fid)
                self.numeric_ids_under_inspection_set = set(self.numeric_ids_under_inspection)

        if self.value_signal_numeric_id not in self.numeric_ids_under_inspection_set:
            raise synthesizeException("signal %s is not in the database" % self.value_signal)

        # extract key from trace
        KEY_VALUE_QUERY = 'SELECT nextval from traces WHERE simulation_time=? AND simulation_trace=? AND numeric_id=?'
        self.cursor.execute(KEY_VALUE_QUERY, (self.value_signal_time, index, self.value_signal_numeric_id))

        value = self.cursor.fetchone()
        if value is None:
            raise synthesizeException("key not found in vcd file as specified time: %d trace: %d numeric_id: %d" % (self.value_signal_time, index, self.value_signal_numeric_id))

        value = value[0]
        value_width = self.signal_properties[self.value_signal_numeric_id]['width']
        if value_width % 8:
            raise synthesizeException("value width must be multiple of byte: %d" % value_width)

        value = value.zfill(value_width)
        value = bytearray(int(value, 2).to_bytes((len(value) + 7) // 8, 'big'))
        value = np.array([value], dtype=np.uint8)

        # extract the leakage
        leakage = np.zeros((len(self.simulation_time_steps),), dtype=np.int)

        if not fastMode:
            # vertical approach assemble leakage over the signals
            for numeric_id in self.numeric_ids_under_inspection:

                signal_leakage = np.zeros((len(self.simulation_time_steps),), dtype=np.int)

                # logger.info("processing signal with numeric id: %d" % (numeric_id))

                SIGNAL_UPDATE_QUERY = 'SELECT simulation_time, nextval from traces WHERE simulation_trace=? AND numeric_id=?  ORDER BY simulation_time ASC'
                nextval_index_old = -1
                nextval_val_old = 0
                for update in self.cursor.execute(SIGNAL_UPDATE_QUERY, (index, numeric_id)):
                    # logger.debug("%s" % (self.simulation_time_to_index[update[0]]))
                    nextval_index = self.simulation_time_to_index[update[0]]
                    nextval_val = hammingWeightFromBitString(update[1])
                    signal_leakage[nextval_index_old:nextval_index + 1] = nextval_val_old
                    nextval_index_old = nextval_index
                    nextval_val_old = nextval_val

                signal_leakage[nextval_index_old:] = nextval_val_old
                leakage += signal_leakage

        else:
            # horizontal mode assemmble state from changes and derive leakage
            # fetch all updates
            SIGNAL_UPDATE_QUERY = 'SELECT simulation_time, numeric_id, nextval from traces WHERE simulation_trace=?  ORDER BY simulation_time ASC'
            logger.info("extracting state updates from database")
            self.cursor.execute(SIGNAL_UPDATE_QUERY, (index, ))
            self.updates = self.cursor.fetchall()

            # umbauen ummappen auf signale die benutzt werden
            state = np.zeros((len(self.signal_properties),), dtype=np.int)

            logger.info("iterating through all state updates")
            nextval_index_old = -1
            for update in self.updates:
                nextval_index = self.simulation_time_to_index[update[0]]
                nextval = hammingWeightFromBitString(update[2])
                numeric_id = update[1]

                # das bremst aus wie noch was
                # check if signal is tracked
                if numeric_id not in self.numeric_ids_under_inspection_set:
                    continue

                # logger.info("index: %d  numeric_id: %d nextval: %d" % (nextval_index, numeric_id, nextval))
                if nextval_index != nextval_index_old:
                    leakage[nextval_index_old:nextval_index + 1] = np.sum(state)
                    nextval_index_old = nextval_index

                state[numeric_id] = nextval

            # last update after loop
            leakage[nextval_index_old:nextval_index + 1] = np.sum(state)

        # this extracts the hamming weight
        if self.leakage == "HammingWeight":
            pass
        elif self.leakage == "HammingDistance":
            # calculate the hamming distance
            shift_leakage = np.roll(leakage, 1)
            leakage = np.abs(leakage[1:] - shift_leakage[1:])
        else:
            raise synthesizeException("undefined leakage model: %s" % self.leakage)

        if self.windowFrom is not None or self.windowTo is not None:
            logger.info("extracting window from leakage %d:%d" % (self.windowFrom, self.windowTo))
            leakage = leakage[self.windowFrom:self.windowTo]

        # dynamic scaling of trace eigentlich sollte man hier nach dem max suchen wenn das kleiner als max wer uint8 alles zu einem uint8

        return Trace(leakage, value)


# if everything fits into ram use fastmode
fastMode = settings["synthesize"]["fastMode"]
leakageModel = settings["synthesize"]["leakageModel"]
traceFileName = settings["synthesize"]["traceFileName"]
value_signal = settings["synthesize"]["value_signal_numeric_id"]
value_signal_time = settings["synthesize"]["value_signal_time"]

# put null in json to load everything
windowFrom = settings["synthesize"]["windowFrom"]
windowTo = settings["synthesize"]["windowTo"]

writeTraces = settings["synthesize"]["writeTraces"]

# create our acquisition setup
aqc = AcquisitionSetupToggle(simulation_trace_max + 1,
                             fileNameDatabase,
                             numeric_ids_under_inspection,
                             leakage=leakageModel,
                             windowFrom=windowFrom,
                             windowTo=windowTo,
                             fastMode=fastMode,
                             value_signal_numeric_id=value_signal,
                             reload_numeric_ids=True,
                             value_signal_time=value_signal_time)

# export traces to container
if writeTraces:
    hdf5_container = Hdf5Container.export(aqc, traceFileName)

# print("trace 0:", aqc[0])
# print("trace 10:", aqc[10])

# so kann man plotten
# plt.plot(aqc[0][0])
# plt.show()

# verwendung mit externem tool
# aqc.generate_trace(1)


logger.info("synthesize traces from database finished")
