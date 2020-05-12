#!/usr/bin/python3
import json
import glob
import logging
import sqlite3
import re
import time

time_start = time.time()

# create a logger
logger = logging.getLogger('parse')
if (logger.hasHandlers()):
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# loading settings from file
settings = None
settingsFile = "./settings.json"
logger.info("loading settings from file: %s" % (settingsFile))
with open("./settings.json") as fid:
    settings = json.load(fid)


class vcdException(Exception):
    pass


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


def buildfromtokens(token):
    collector = []
    while(True):
        current_token = next(token)
        if(current_token == "$end"):
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected


def identifierToName(vcdHeader):
    blah = {}
    for scope in vcdHeader["scope"].keys():
        for var in vcdHeader["scope"][scope]:
            # Ähhhh vielleicht sollte man identifier mit dem scope hashen???
            blah[var["identifier"]] = var["name"]
    return blah


# if everything fits into ram
fastMode = settings["parse"]["fastMode"]
# globbing for vcd files
vcdFiles = glob.glob(settings["parse"]["vcdGlob"])


# create database connection
conn = sqlite3.connect(settings["parse"]["database"])
cursor = conn.cursor()


# create table in database
# Create table
DROP_TABLE_TRACES_QUERY = 'DROP TABLE IF EXISTS traces'
cursor.execute(DROP_TABLE_TRACES_QUERY)
DROP_TABLE_SIGNALS_QUERY = 'DROP TABLE IF EXISTS signals'
cursor.execute(DROP_TABLE_SIGNALS_QUERY)
conn.commit()


###################################################################################################
# iterate over all vcd files
for (simulation_trace, vcdFile) in enumerate(vcdFiles):

    logger.info("processing vcd file (%d/%d): %s" % (simulation_trace + 1, len(vcdFiles), vcdFile))

    fid = open(vcdFile)
    tokens = token_generator(fid)

    # reset all header informations
    vcdHeader = {}
    vcdHeader["scope"] = {}
    currScope = []

    logger.info("extracting header")
    # extract header
    while(True):
        # extract header from value change dump
        keyword = next(tokens)
        # process extracted data
        if(keyword == "$comment"):
            comment = buildfromtokens(tokens)
            # logger.debug("comment: %s" % comment)
            vcdHeader[keyword[1:]] = comment

        if(keyword == "$date"):
            date = buildfromtokens(tokens)
            # logger.debug("date: %s" % date)
            vcdHeader[keyword[1:]] = date

        elif(keyword == "$version"):
            version = buildfromtokens(tokens)
            # logger.debug("version: %s" % version)
            vcdHeader[keyword[1:]] = version

        elif(keyword == "$timescale"):
            timescale = buildfromtokens(tokens)
            # logger.debug("timescale: %s" % timescale)
            vcdHeader[keyword[1:]] = timescale

        elif(keyword == "$scope"):
            scope = buildfromtokens(tokens)
            currScope.append(scope)
            # logger.debug("->".join(currScope))
            vcdHeader["scope"]["->".join(currScope)] = []

        elif(keyword == "$upscope"):
            upscope = buildfromtokens(tokens)
            # logger.debug("upscope: %s" % upscope)
            currScope.pop()

        elif(keyword == "$var"):
            var = buildfromtokens(tokens)
            # logger.debug("var: %s" % var)
            match = re.match("^wire\\s+([0-9]+)\\s+(\\S*)\\s+(.*)$", var)
            if match is not None:
                width = match.groups()[0]
                identifier = match.groups()[1]
                name = match.groups()[2]
                # logger.debug("width: %s\tidentifier: %s\tname: %s" % (width, identifier, name))
                # logger.debug(width)
            else:
                raise vcdException("unable to parse variable: %s" % var)

            vcdHeader["scope"]["->".join(currScope)].append({"name": name, "width": int(width), "identifier": identifier})

        elif(keyword == "$enddefinitions"):
            enddefinition = buildfromtokens(tokens)
            # logger.debug("enddefinition: %s" % enddefinition)
            break

        else:
            raise vcdException("undefined keyword: %s" % keyword)

    # fuck the verilog identifiers
    iton = identifierToName(vcdHeader)

    # the signal names must be the same for all simulations
    escaped_signal_names = ", ".join(['\'' + i + '\'' + ' TEXT' for i in list(iton.values())])
    CREATE_TABLE_TRACES_QUERY = 'CREATE TABLE IF NOT EXISTS traces (simulation_time INTEGER, simulation_trace INTEGER, %s)' % escaped_signal_names
    cursor.execute(CREATE_TABLE_TRACES_QUERY)

    CREATE_TABLE_SIGNAL_QUERY = 'CREATE TABLE IF NOT EXISTS signals (name TEXT, width INTEGER, scope TEXT)'
    cursor.execute(CREATE_TABLE_SIGNAL_QUERY)

    INSERT_TABLE_SIGNAL_QUERY = 'INSERT INTO signals (name,width,scope) VALUES (?,?,?)'
    for scope in list(vcdHeader["scope"].keys()):
        for signal in vcdHeader["scope"][scope]:
            cursor.execute(INSERT_TABLE_SIGNAL_QUERY, (signal["name"], signal["width"], scope))
    conn.commit()

    # fill signal data to traces
    simulation_time = 0
    simulation_time_old = 0

    INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY = 'INSERT INTO traces (simulation_time,simulation_trace) VALUES (?,?)'
    # cursor.execute(INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY, (simulation_time, simulation_trace))
    # conn.commit()

    UPDATE_TABLE_TRACES_SIGNAL_QUERY = 'UPDATE traces SET \'%s\'=? WHERE simulation_time=? AND simulation_trace=?'
    # cursor.execute('UPDATE_TABLE_TRACES_SIGNAL_QUERY' % (iton[var]), (val,simulation_time,simulation_trace))
    # conn.commit

    state = {}

    trace = []
    colNameToIndex = ["simulation_time", "simulation_trace"] + list(iton.values())
    colNameToIndex = {i[1]: i[0] for i in enumerate(colNameToIndex)}
    traceSample = ["OIDA"] * len(colNameToIndex)

    logger.info("extracting signal values")
    # extract simulation values
    for current_token in tokens:
        # logger.debug(current_token)

        match_time = re.match("^#([0-9]+)$", current_token)
        match_update_scalar = re.match("^([01xXzZ])(.+)$", current_token)
        match_update_vector = re.match("^([bB][01xXzZ]+)$", current_token)
        match_dumpvars = re.match("^(\\$dumpvars)$", current_token)

        if match_time is not None:
            simulation_time_old = simulation_time
            simulation_time = int(match_time.groups()[0])

            logger.debug("-" * 100)
            logger.debug("time: %s" % simulation_time)

            if not fastMode:
                cursor.execute(INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY, (simulation_time, simulation_trace))
                # copy the previous row to the next row
                if simulation_time != 0:
                    UPDATE_TABLE_TRACES_STATE_QUERY = 'UPDATE traces SET %s WHERE simulation_time=? AND simulation_trace=?' % \
                        (", ".join(['\'' + i + '\'' + '=?' for i in list(state.keys())]))
                    cursor.execute(UPDATE_TABLE_TRACES_STATE_QUERY, (list(state.values()) + [simulation_time] + [simulation_trace]))
                    # for signal in state.keys():
                    #     cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (signal), (state[signal], simulation_time, simulation_trace))
            else:
                if len(trace) == 0:
                    trace.append(traceSample.copy())
                else:
                    trace.append(trace[-1].copy())
                trace[-1][colNameToIndex["simulation_time"]] = simulation_time
                trace[-1][colNameToIndex["simulation_trace"]] = simulation_trace

        elif match_dumpvars is not None:
            # extract initial value
            for dumpvar_token in tokens:
                if(dumpvar_token == "$end"):
                    break
                match_dumpvar_scalar = re.match("^([01xXzZ])(.+)$", dumpvar_token)
                match_dumpvar_vector = re.match("^([bB][01xXzZ]+)$", dumpvar_token)
                if match_dumpvar_scalar is not None:
                    # update scalar signal values
                    val = match_dumpvar_scalar.groups()[0]
                    var = match_dumpvar_scalar.groups()[1]
                    logger.debug("update: %s ---> %s" % (iton[var], val))

                    if not fastMode:
                        state[iton[var]] = val
                        cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton[var]), (val, simulation_time, simulation_trace))
                    else:
                        trace[-1][colNameToIndex[iton[var]]] = val

                elif match_dumpvar_vector is not None:
                    # update vector signal values
                    val = match_dumpvar_vector.groups()[0]
                    # remove b prefix
                    val = val[1:]
                    var = next(tokens)
                    logger.debug("update: %s ---> %s" % (iton[var], val))

                    if not fastMode:
                        state[iton[var]] = val
                        cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton[var]), (val, simulation_time, simulation_trace))
                    else:
                        trace[-1][colNameToIndex[iton[var]]] = val

                else:
                    raise vcdException("unable to parse variable: %s" % dumpvar_token)

        elif match_update_scalar is not None:
            # update scalar signal values
            val = match_update_scalar.groups()[0]
            var = match_update_scalar.groups()[1]
            logger.debug("update: %s ---> %s" % (iton[var], val))

            if not fastMode:
                state[iton[var]] = val
                cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton[var]), (val, simulation_time, simulation_trace))
            else:
                trace[-1][colNameToIndex[iton[var]]] = val

        elif match_update_vector is not None:
            # update vector signal values
            val = match_update_vector.groups()[0]
            # remove b prefix
            val = val[1:]
            var = next(tokens)
            logger.debug("update: %s ---> %s" % (iton[var], val))

            if not fastMode:
                state[iton[var]] = val
                cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton[var]), (val, simulation_time, simulation_trace))
            else:
                trace[-1][colNameToIndex[iton[var]]] = val

        else:
            raise vcdException("unable to parse variable: %s" % current_token)

    # batch insert to database
    if fastMode:
        INSERT_TRACE_QUERY = 'INSERT INTO traces VALUES (%s)' % \
            (", ".join(["?" for i in list(colNameToIndex.keys())]))
        cursor.executemany(INSERT_TRACE_QUERY, trace)
        trace = []

    conn.commit()
    fid.close()


###################################################################################################
# print(vcdHeader)
conn.commit()
conn.close()

time_finish = time.time()
logger.info("conversion from vcd to database finished in %d seconds" % (time_finish - time_start))
