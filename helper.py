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

import os
import json
import re


def loadSettings(settingsFile):

    with open(settingsFile) as fid:
        settings = json.load(fid)

    return settings


def validateSettings(settings):
    knownKeys = []
    knownKeys.append("vcdGlob")
    knownKeys.append("pickleGlob")
    knownKeys.append("signalsFileNameLiterals")
    knownKeys.append("signalsFileName")
    knownKeys.append("signalPropertiesFile")
    knownKeys.append("leakageModel")
    knownKeys.append("window")
    knownKeys.append("windowFrom")
    knownKeys.append("windowTo")
    knownKeys.append("valueExtractFunction")
    knownKeys.append("writeTraces")
    knownKeys.append("writeTracesBatchSize")
    knownKeys.append("traceFileName")
    knownKeys.append("allign")
    knownKeys.append("downsample")
    knownKeys.append("format")

    for i in knownKeys:
        if i not in settings.keys():
            raise Exception("You screwed up your settings")

    return settings


def prepareSettings(settingsFile, settings):

    # extract path to settings file
    settingsFileLocation = os.path.abspath(settingsFile)
    settingsFilePath = os.path.dirname(settingsFileLocation) + "/"

    # translate all paths to relativ paths
    settings["vcdGlob"] = settingsFilePath + settings["vcdGlob"]
    settings["pickleGlob"] = settingsFilePath + settings["pickleGlob"]
    settings["signalsFileNameLiterals"] = settingsFilePath + settings["signalsFileNameLiterals"]
    settings["signalsFileName"] = settingsFilePath + settings["signalsFileName"]
    settings["signalPropertiesFile"] = settingsFilePath + settings["signalPropertiesFile"]
    settings["traceFileName"] = settingsFilePath + settings["traceFileName"]
    settings["settingsFilePath"] = settingsFilePath
    settings["settingsFileLocation"] = settingsFileLocation

    return settings


def natural_sort_key(s):

    # sort naturaly not in aphabetic order
    natural_sort_regex = re.compile("([0-9]+)")

    return [int(part) if part.isdigit() else part.lower() for part in natural_sort_regex.split(s)]
