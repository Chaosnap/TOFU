#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: parse.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import argparse
import json
import glob
import logging
import re
import time
import pickle
import progressbar
import os

time_start = time.time()

# create a logger
logger = logging.getLogger("parse")
if logger.hasHandlers():
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# loading settings from file
settingsFile = "./settings.json"
parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=False)
parser.add_argument("-l", "--loglevel", type=str, help="specify loglevel", required=False, default="info")
namespace = parser.parse_args()

# parse loglevel
loglevel = namespace.loglevel
numeric_log_id = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_log_id, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logger.setLevel(numeric_log_id)

if namespace.settings is not None:
    settingsFile = namespace.settings
settings = None
logger.info("loading settings from file: %s" % (settingsFile))
with open(settingsFile) as fid:
    settings = json.load(fid)
# extract path to settings file
settingsFileLocation = os.path.abspath(settingsFile)
settingsFilePath = os.path.dirname(settingsFileLocation) + "/"

# compiled regexes for faster matching tested to be faster
re_match_time = re.compile("^#([0-9]+)$")
re_match_update_scalar = re.compile("^([01xXzZuU])(.+)$")
re_match_update_vector = re.compile("^([bB][01xXzZuU]+)$")
re_match_dumpvars = re.compile("^(\\$dumpvars)$")
re_match_dumpvar_scalar = re.compile("^([01xXzZuU])(.+)$")
re_match_dumpvar_vector = re.compile("^([bB][01xXzZuU]+)$")


def token_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


def buildfromtokens(token):
    collector = []
    while True:
        current_token = next(token)
        if current_token == "$end":
            break
        collector.append(current_token)
    collected = " ".join(collector)
    return collected


# def identifierToName(vcdHeader):
#     blah = {}
#     for scope in vcdHeader["scope"].keys():
#         for var in vcdHeader["scope"][scope]:
#             # Ähhhh vielleicht sollte man identifier mit dem scope hashen???
#             blah[var["identifier"]] = var["name"]
#     return blah


def identifierToNames(vcdHeader):
    blah = {}
    for scope in vcdHeader["scope"].keys():
        for var in vcdHeader["scope"][scope]:
            if var["identifier"] in blah:
                blah[var["identifier"]].append({"name": var["name"], "width": var["width"], "scope": scope})
            else:
                blah[var["identifier"]] = [{"name": var["name"], "width": var["width"], "scope": scope}]

    # assign every identifier a numeric id
    for numeric_id, identifier in enumerate(blah):
        blah[identifier] = [{"name": i["name"], "width": i["width"], "scope": i["scope"], "numeric_id": numeric_id} for i in blah[identifier]]
    return blah


# sort naturaly not in aphabetic order
def natural_sort_key(s):
    natural_sort_regex = re.compile("([0-9]+)")
    return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]


# globbing for vcd files
vcdFiles = glob.glob(settingsFilePath + settings["vcdGlob"])
vcdFiles = sorted(vcdFiles, key=natural_sort_key)

signalPropertiesFile = settingsFilePath + settings["signalPropertiesFile"]
traceFormat = settings["format"]

iddict = {}

signal_properties = []

###################################################################################################
# iterate over all vcd files
# for (simulation_trace, vcdFile) in enumerate(vcdFiles):
widgets = [
    "parse" + " |",
    progressbar.Percentage(),
    progressbar.Bar(),
    progressbar.FormatLabel("%(value)d vcd"),
    "/%d |" % (len(vcdFiles)),
    progressbar.AdaptiveETA(),
]

for simulation_trace in progressbar.progressbar(range(len(vcdFiles)), widgets=widgets):
    vcdFile = vcdFiles[simulation_trace]

    logger.info("processing vcd file (%d/%d): %s" % (simulation_trace + 1, len(vcdFiles), vcdFile))

    fid = open(vcdFile)

    tokens = token_generator(fid)

    # reset all header informations
    vcdHeader = {}
    vcdHeader["scope"] = {}
    currScope = []

    logger.info("extracting header")
    # extract header
    while True:
        # extract header from value change dump
        keyword = next(tokens)
        # process extracted data
        if keyword == "$comment":
            comment = buildfromtokens(tokens)
            # logger.debug("comment: %s" % comment)
            vcdHeader[keyword[1:]] = comment

        elif keyword == "$date":
            date = buildfromtokens(tokens)
            # logger.debug("date: %s" % date)
            vcdHeader[keyword[1:]] = date

        elif keyword == "$version":
            version = buildfromtokens(tokens)
            # logger.debug("version: %s" % version)
            vcdHeader[keyword[1:]] = version

        elif keyword == "$timescale":
            timescale = buildfromtokens(tokens)
            # logger.debug("timescale: %s" % timescale)
            vcdHeader[keyword[1:]] = timescale

        elif keyword == "$scope":
            scope = buildfromtokens(tokens)
            currScope.append(scope)
            # logger.debug("->".join(currScope))
            # ??? wtf scoping verilator
            currScopeKey = "->".join(currScope)
            if currScopeKey not in vcdHeader["scope"].keys():
                vcdHeader["scope"][currScopeKey] = []

        elif keyword == "$upscope":
            upscope = buildfromtokens(tokens)
            # logger.debug("upscope: %s" % upscope)
            currScope.pop()

        elif keyword == "$var":
            var = buildfromtokens(tokens)
            # logger.debug("var: %s" % var)
            match = re.match("^(wire|reg|logic|parameter|int|bit|byte)\\s+([0-9]+)\\s+(\\S*)\\s+(.*)$", var)
            if match is not None:
                dtype = match.groups()[0]
                width = match.groups()[1]
                identifier = match.groups()[2]
                name = match.groups()[3]
                # logger.debug("scope: %s\twidth: %s\tidentifier: \t%s dtype: %s\tname: %s" % ("->".join(currScope), width, identifier, dtype, name))
                # logger.debug(width)
            else:
                raise Exception("unable to parse variable: %s" % var)

            vcdHeader["scope"]["->".join(currScope)].append({"name": name, "width": int(width), "identifier": identifier})

        elif keyword == "$enddefinitions":
            enddefinition = buildfromtokens(tokens)
            # logger.debug("enddefinition: %s" % enddefinition)
            break

        else:
            raise Exception("undefined keyword: %s" % keyword)

    # replace the verilog identifiers
    # iton = identifierToName(vcdHeader)
    itons = identifierToNames(vcdHeader)

    if simulation_trace == 0:
        for identifier in itons:
            for signal in itons[identifier]:
                signal_properties.append((signal["numeric_id"], signal["name"], signal["width"], signal["scope"]))
                iddict[signal["scope"] + "->" + signal["name"]] = signal["numeric_id"]

        # pickle that shit
        with open(signalPropertiesFile, "wb") as f:
            logger.info("pickling signal properties to file: %s" % (signalPropertiesFile))
            pickle.dump(signal_properties, f, pickle.HIGHEST_PROTOCOL)

        # pickle the metadata only required by tueisec format
        if traceFormat == "tueisec":
            exclude_keys = {"scope"}
            vcd_meta = {x: vcdHeader[x] for x in vcdHeader if x not in exclude_keys}
            with open(signalPropertiesFile.rsplit(".", 1)[0] + "_meta.pickle", "wb") as f:
                logger.info("pickling signal properties meta to file: %s" % (signalPropertiesFile.rsplit(".", 1)[0] + "_meta.pickle"))
                pickle.dump(vcd_meta, f, pickle.HIGHEST_PROTOCOL)

    # get num id in all but the first trace
    # fix this

    # fill signal data to traces
    simulation_time = 0
    simulation_time_old = 0

    updates = []

    logger.info("extracting signal values")
    # extract simulation values
    for current_token in tokens:
        # logger.debug(current_token)

        match_update_scalar = re_match_update_scalar.match(current_token)
        if match_update_scalar is not None:
            # update scalar signal values
            val = match_update_scalar.groups()[0]
            var = match_update_scalar.groups()[1]
            logger.debug("update: %s ---> %s" % (var, val))

            signal_name = itons[var][0]["name"]
            signal_scope = itons[var][0]["scope"]
            numeric_id = iddict[signal_scope + "->" + signal_name]
            updates.append((simulation_time, numeric_id, val))
            match_update_scalar = None
            continue

        match_update_vector = re_match_update_vector.match(current_token)
        if match_update_vector is not None:
            # update vector signal values
            val = match_update_vector.groups()[0]
            # remove b prefix
            val = val[1:]
            var = next(tokens)
            logger.debug("update: %s ---> %s" % (var, val))

            signal_name = itons[var][0]["name"]
            signal_scope = itons[var][0]["scope"]
            numeric_id = iddict[signal_scope + "->" + signal_name]
            updates.append((simulation_time, numeric_id, val))
            match_update_vector = None
            continue

        match_time = re_match_time.match(current_token)
        if match_time is not None:
            simulation_time_old = simulation_time
            simulation_time = int(match_time.groups()[0])

            logger.debug("-" * 100)
            logger.debug("time: %s" % simulation_time)
            match_time = None
            continue

        match_dumpvars = re_match_dumpvars.match(current_token)
        if match_dumpvars is not None:
            # extract initial value
            for dumpvar_token in tokens:
                if dumpvar_token == "$end":
                    break

                match_dumpvar_scalar = re_match_dumpvar_scalar.match(dumpvar_token)
                match_dumpvar_vector = re_match_dumpvar_vector.match(dumpvar_token)

                if match_dumpvar_scalar is not None:
                    # update scalar signal values
                    val = match_dumpvar_scalar.groups()[0]
                    var = match_dumpvar_scalar.groups()[1]
                    logger.debug("update: %s ---> %s" % (var, val))

                    signal_name = itons[var][0]["name"]
                    signal_scope = itons[var][0]["scope"]
                    numeric_id = iddict[signal_scope + "->" + signal_name]
                    updates.append((simulation_time, numeric_id, val))

                elif match_dumpvar_vector is not None:
                    # update vector signal values
                    val = match_dumpvar_vector.groups()[0]
                    # remove b prefix
                    val = val[1:]
                    var = next(tokens)
                    logger.debug("update: %s ---> %s" % (var, val))

                    signal_name = itons[var][0]["name"]
                    signal_scope = itons[var][0]["scope"]
                    numeric_id = iddict[signal_scope + "->" + signal_name]
                    updates.append((simulation_time, numeric_id, val))

                else:
                    raise Exception("unable to parse variable: %s" % dumpvar_token)
            match_dumpvars = None
            continue

        raise Exception("unable to parse variable: %s" % current_token)

    # batch insert to database
    pickleFile = re.sub(r".vcd$", r".pickle", vcdFile)
    logger.info("pickling updates to file: %s" % (pickleFile))
    # pickle that shit
    with open(pickleFile, "wb") as f:
        pickle.dump(updates, f, pickle.HIGHEST_PROTOCOL)

    updates = []
    fid.close()


###################################################################################################
# print(vcdHeader)

time_finish = time.time()
logger.info("conversion from vcd to pickle finished in %f seconds" % (time_finish - time_start))
