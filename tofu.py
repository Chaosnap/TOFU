#!/bin/python3
import sqlite3
import re


class vcdException(Exception):
    pass


def buildfromtokens(token):
    collector = []
    while(True):
        current_token = next(token)
        if(current_token == "$end"):
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected


def identifierToName(vcdHeader, scope):
    blah = {}
    for var in vcdHeader["scope"][scope]:
        blah[var["identifier"]] = var["name"]
    return blah


fileName = "./dummy-vivado.vcd"
# fileName = "./dummy-modelsim.vcd"
fid = open(fileName)

conn = sqlite3.connect(re.sub("vcd", "db", fileName))
cursor = conn.cursor()


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


tokens = token_generator(fid)


vcdHeader = {}
vcdHeader["scope"] = {}
currScope = []

# extract header
while(True):
    # extract header from value change dump
    keyword = next(tokens)
    # process extracted data
    if(keyword == "$comment"):
        comment = buildfromtokens(tokens)
        # print("comment: %s" % comment)
        vcdHeader[keyword[1:]] = comment

    if(keyword == "$date"):
        date = buildfromtokens(tokens)
        # print("date: %s" % date)
        vcdHeader[keyword[1:]] = date

    elif(keyword == "$version"):
        version = buildfromtokens(tokens)
        # print("version: %s" % version)
        vcdHeader[keyword[1:]] = version

    elif(keyword == "$timescale"):
        timescale = buildfromtokens(tokens)
        # print("timescale: %s" % timescale)
        vcdHeader[keyword[1:]] = timescale

    elif(keyword == "$scope"):
        scope = buildfromtokens(tokens)
        currScope.append(scope)
        # print("->".join(currScope))
        vcdHeader["scope"]["->".join(currScope)] = []

    elif(keyword == "$upscope"):
        upscope = buildfromtokens(tokens)
        # print("upscope: %s" % upscope)
        currScope.pop()

    elif(keyword == "$var"):
        var = buildfromtokens(tokens)
        # print("var: %s" % var)
        match = re.match("^wire\\s+([0-9]+)\\s+(\\S*)\\s+(.*)$", var)
        if match is not None:
            width = match.groups()[0]
            identifier = match.groups()[1]
            name = match.groups()[2]
            # print("width: %s\tidentifier: %s\tname: %s" % (width, identifier, name))
            # print(width)
        else:
            raise vcdException("unable to parse variable: %s" % var)

        vcdHeader["scope"]["->".join(currScope)].append({"name": name, "width": int(width), "identifier": identifier})

    elif(keyword == "$enddefinitions"):
        enddefinition = buildfromtokens(tokens)
        # print("enddefinition: %s" % enddefinition)
        break

    else:
        raise vcdException("undefined keyword: %s" % keyword)


# fuck the verilog identifiers
# scope = "module lwc_tb->module uut->module Inst_Cipher"
scope = "module LWC_TB->module uut->module Inst_Cipher"
blah = identifierToName(vcdHeader, scope)


def iton(x):
    return blah[x]


def bintohex(x):
    print(x)
    if re.match("^([bB][xXzZ]+)$", x):
        return x[1:]
    else:
        return hex(int(x[1:], 2))


# create table in database
# Create table
DROP_TABLE_TRACES_QUERY = 'DROP TABLE IF EXISTS traces'
cursor.execute(DROP_TABLE_TRACES_QUERY)
DROP_TABLE_SIGNALS_QUERY = 'DROP TABLE IF EXISTS signals'
cursor.execute(DROP_TABLE_SIGNALS_QUERY)
conn.commit()

escaped_signal_names = ", ".join(['\'' + i + '\'' + ' TEXT' for i in list(blah.values())])
CREATE_TABLE_TRACES_QUERY = 'CREATE TABLE traces (simulation_time INTEGER, simulation_trace INTEGER, %s)' % escaped_signal_names
cursor.execute(CREATE_TABLE_TRACES_QUERY)

CREATE_TABLE_SIGNAL_QUERY = 'CREATE TABLE signals (name TEXT, width INTEGER, scope TEXT)'
cursor.execute(CREATE_TABLE_SIGNAL_QUERY)

INSERT_TABLE_SIGNAL_QUERY = 'INSERT INTO signals VALUES (%s)'
for scope in list(vcdHeader["scope"].keys()):
    for signal in vcdHeader["scope"][scope]:
        escaped_signal_properties = '\'' + signal["name"] + '\',\'' + str(signal["width"]) + '\' ,\'' + scope + '\''
        cursor.execute(INSERT_TABLE_SIGNAL_QUERY % (escaped_signal_properties))
conn.commit()

# fill signal data to traces
simulation_time = 0
simulation_time_old = 0
simulation_trace = 1
INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY = 'INSERT INTO traces (simulation_time,simulation_trace) VALUES (?,?)'
# cursor.execute(INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY, (simulation_time, simulation_trace))
# conn.commit()

UPDATE_TABLE_TRACES_SIGNAL_QUERY = 'UPDATE traces SET \'%s\'=? WHERE simulation_time=? AND simulation_trace=?'
# cursor.execute('UPDATE_TABLE_TRACES_SIGNAL_QUERY' % (iton(var)), (val,simulation_time,simulation_trace))
# conn.commit

# extract simulation values
for current_token in tokens:
    # print(current_token)

    match_time = re.match("^#([0-9]+)$", current_token)
    match_update_scalar = re.match("^([01xXzZ])(.+)$", current_token)
    match_update_vector = re.match("^([bB][01xXzZ]+)$", current_token)
    match_dumpvars = re.match("^(\\$dumpvars)$", current_token)

    if match_time is not None:
        simulation_time_old = simulation_time
        simulation_time = int(match_time.groups()[0])
        print("-" * 100)
        print("time: %s" % simulation_time)
        cursor.execute(INSERT_TABLE_TRACES_SIMULATION_TIME_QUERY, (simulation_time, simulation_trace))

        # copy the previous row to the next row
        if simulation_time != 0:
            pass

    elif match_dumpvars is not None:
        # extract initial value
        for dumpvar_token in tokens:
            if(dumpvar_token == "$end"):
                break
            match_dumpvar_scalar = re.match("^([01xXzZ])(.+)$", dumpvar_token)
            match_dumpvar_vector = re.match("^([bB][01xXzZ]+)$", dumpvar_token)
            if match_dumpvar_scalar is not None:
                # update signal values
                val = match_dumpvar_scalar.groups()[0]
                var = match_dumpvar_scalar.groups()[1]
                print("update: %s ---> %s" % (iton(var), val))
                cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton(var)), (val, simulation_time, simulation_trace))

            elif match_dumpvar_vector is not None:
                val = match_dumpvar_vector.groups()[0]
                var = next(tokens)
                print("update: %s ---> %s" % (iton(var), val))
                cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton(var)), (val, simulation_time, simulation_trace))

            else:
                raise vcdException("unable to parse variable: %s" % dumpvar_token)

    elif match_update_scalar is not None:
        # update signal values
        val = match_update_scalar.groups()[0]
        var = match_update_scalar.groups()[1]
        # update signal values
        print("update: %s ---> %s" % (iton(var), val))
        cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton(var)), (val, simulation_time, simulation_trace))

    elif match_update_vector is not None:
        val = match_update_vector.groups()[0]
        var = next(tokens)
        # update signal values
        print("update: %s ---> %s" % (iton(var), val))
        cursor.execute(UPDATE_TABLE_TRACES_SIGNAL_QUERY % (iton(var)), (val, simulation_time, simulation_trace))

    else:
        raise vcdException("unable to parse variable: %s" % current_token)


# print(vcdHeader)
conn.commit()
conn.close()
