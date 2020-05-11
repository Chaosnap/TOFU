#!/usr/bin/python3
import logging
import sqlite3
import json
import os.path

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


SIGNAL_VALUE_QUERY = 'SELECT %s from traces WHERE simulation_time=? AND simulation_trace=?' % \
    (", ".join(["\"" + i + "\"" for i in list(signals.keys())]))
cursor.execute(SIGNAL_VALUE_QUERY, (0, 0))
blah = cursor.fetchone()

#extrac partition value i.e. key

conn.commit()
conn.close()
logger.info("synthesize traces from database finished")
