#!/usr/bin/python3
# -*- coding: utf-8 -*-
# This file is part of TOFU
#
# TOFU is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2022 (C)
# Technical University of Munich
# TUM Department of Electrical and Computer Engineering
# Chair of Security in Information Technology
# Written by the following authors: Michael Gruber

import argparse
import glob
import logging
import re
import time
import pickle
import helper
import os

# loading settings from file
parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=True)
parser.add_argument("-l", "--loglevel", type=str, help="specify loglevel", required=False, default="info")
namespace = parser.parse_args()

# create a logger
logger = logging.getLogger(os.path.basename(__file__))
if logger.hasHandlers():
    logger.handlers.clear()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# parse loglevel
loglevel = namespace.loglevel
numeric_log_id = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_log_id, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logger.setLevel(numeric_log_id)

# prepare settings dictionary
settingsFile = namespace.settings
logger.info("loading settings from file: %s" % (settingsFile))
settings = helper.loadSettings(settingsFile)
settings = helper.validateSettings(settings, mode="tofu")
settings = helper.prepareSettings(settingsFile, settings, mode="tofu")


# compiled regexes for faster matching tested to be faster
re_match_time = re.compile(r"^#([0-9]+)$")
re_match_scalar_or_vector = re.compile(r"^([bB]{0,1}[01xXzZuU]+)\s*([^\s]+)$")
re_match_scalar = re.compile(r"^([01xXzZuU])(.+)$")
re_match_vector = re.compile(r"^([bB][01xXzZuU]+)\s+(.*)$")
re_match_dumpvars = re.compile(r"^(\$dumpvars)$")
re_match_end = re.compile(r"^(\$end)$")
re_match_variable = re.compile(r"^(wire|reg|logic|parameter|int|bit|byte)\s+([0-9]+)\s+(\S*)\s+(.*)$")

time_start = time.time()


def word_generator(fid):
    for line in fid:
        for word in line.split():
            yield word


def line_generator(fid):
    for line in fid:
        yield line


def buildfromwords(word):
    collector = []
    while True:
        current_word = next(word)
        if current_word == "$end":
            break
        collector.append(current_word)
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


# globbing for vcd files
vcdFiles = glob.glob(settings["vcdGlob"])
vcdFiles = sorted(vcdFiles, key=helper.natural_sort_key)

signal_properties = []

###################################################################################################
# iterate over all vcd files
# for (simulation_trace, vcdFile) in enumerate(vcdFiles):

for simulation_trace, vcdFile in helper.progressbar(vcdFiles, logger=logger):
    logger.info("processing vcd file (%d/%d): %s" % (simulation_trace + 1, len(vcdFiles), vcdFile))

    fid = open(vcdFile)

    words = word_generator(fid)
    lines = line_generator(fid)

    # reset all header informations
    vcdHeader = {}
    vcdHeader["scope"] = {}
    currScope = []

    logger.info("extracting header")
    # extract header
    while True:
        # extract header from value change dump
        keyword = next(words)
        # process extracted data
        if keyword == "$comment":
            comment = buildfromwords(words)
            # logger.debug("comment: %s" % comment)
            vcdHeader[keyword[1:]] = comment

        elif keyword == "$date":
            date = buildfromwords(words)
            # logger.debug("date: %s" % date)
            vcdHeader[keyword[1:]] = date

        elif keyword == "$version":
            version = buildfromwords(words)
            # logger.debug("version: %s" % version)
            vcdHeader[keyword[1:]] = version

        elif keyword == "$timescale":
            timescale = buildfromwords(words)
            # logger.debug("timescale: %s" % timescale)
            vcdHeader[keyword[1:]] = timescale

        elif keyword == "$scope":
            scope = buildfromwords(words)
            currScope.append(scope)
            # logger.debug("->".join(currScope))
            # ??? wtf scoping verilator
            currScopeKey = "->".join(currScope)
            if currScopeKey not in vcdHeader["scope"].keys():
                vcdHeader["scope"][currScopeKey] = []

        elif keyword == "$upscope":
            upscope = buildfromwords(words)
            # logger.debug("upscope: %s" % upscope)
            currScope.pop()

        elif keyword == "$var":
            var = buildfromwords(words)
            # logger.debug("var: %s" % var)
            match = re_match_variable.match(var)
            if match is not None:
                (dtype, width, identifier, name) = match.groups()
                # logger.debug("scope: %s\twidth: %s\tidentifier: \t%s dtype: %s\tname: %s" % ("->".join(currScope), width, identifier, dtype, name))
                # logger.debug(width)
            else:
                raise Exception("unable to parse variable: %s" % var)

            vcdHeader["scope"]["->".join(currScope)].append({"name": name, "width": int(width), "identifier": identifier})

        elif keyword == "$enddefinitions":
            enddefinition = buildfromwords(words)
            # logger.debug("enddefinition: %s" % enddefinition)
            break

        else:
            raise Exception("undefined keyword: %s" % keyword)

    # replace the verilog identifiers
    # iton = identifierToName(vcdHeader)
    itons = identifierToNames(vcdHeader)

    if simulation_trace == 0:
        # iddict = dict()
        for identifier in itons:
            for signal in itons[identifier]:
                signal_properties.append((signal["numeric_id"], signal["name"], signal["width"], signal["scope"]))
                # iddict[signal["scope"] + "->" + signal["name"]] = signal["numeric_id"]

        # pickle that shit
        with open(settings["signalPropertiesFile"], "wb") as f:
            logger.info("pickling signal properties to file: %s" % (settings["signalPropertiesFile"]))
            pickle.dump(signal_properties, f, pickle.HIGHEST_PROTOCOL)

        # pickle the metadata only required by tueisec format
        if settings["format"] == "tueisec":
            exclude_keys = {"scope"}
            vcd_meta = {x: vcdHeader[x] for x in vcdHeader if x not in exclude_keys}
            with open(settings["signalPropertiesFile"].rsplit(".", 1)[0] + "_meta.pickle", "wb") as f:
                logger.info("pickling signal properties meta to file: %s" % (settings["signalPropertiesFile"].rsplit(".", 1)[0] + "_meta.pickle"))
                pickle.dump(vcd_meta, f, pickle.HIGHEST_PROTOCOL)

    # get num id in all but the first trace
    # fix this

    # fill signal data to traces
    simulation_time = 0
    updates = []
    updates_append = updates.append

    logger.info("extracting signal values")
    # extract simulation values
    for line in lines:
        # logger.debug(line)

        match_update = re_match_scalar_or_vector.match(line)
        if match_update is not None:
            # update scalar signal values
            (val, var) = match_update.groups()
            # logger.debug("update: %s ---> %s" % (var, val))

            numeric_id = itons[var][0]["numeric_id"]
            # interpret all values despite 1 as 0 and remove b prefix for vectors
            val = int(val.upper().replace("B", "").replace("X", "0").replace("U", "0").replace("Z", "0"), 2)
            updates_append((simulation_time, numeric_id, val))
            match_update = None
            continue

        match_time = re_match_time.match(line)
        if match_time is not None:
            simulation_time = int(match_time.groups()[0])

            # logger.debug("-" * 100)
            # logger.debug("time: %s" % simulation_time)
            match_time = None
            continue

        match_dumpvars = re_match_dumpvars.match(line)
        if match_dumpvars is not None:
            # extract initial value
            while True:
                line = next(lines)
                if re_match_end.match(line) is not None:
                    break

                match_update = re_match_scalar_or_vector.match(line)
                if match_update is not None:
                    # update scalar signal values
                    (val, var) = match_update.groups()
                    # logger.debug("update: %s ---> %s" % (var, val))

                    numeric_id = itons[var][0]["numeric_id"]
                    # interpret all values despite 1 as 0 and remove b prefix for vectors
                    val = int(val.upper().replace("B", "").replace("X", "0").replace("U", "0").replace("Z", "0"), 2)
                    updates_append((simulation_time, numeric_id, val))
                    match_update = None
                    continue

                raise Exception("unable to parse line: %s" % line)

            match_dumpvars = None
            continue

        raise Exception("unable to parse line: %s" % line)

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
