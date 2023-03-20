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

import matplotlib.pyplot as plt
import argparse
import json
from lascar.tools.aes import sbox
from lascar.container import Hdf5Container
from lascar.engine import CpaEngine
from lascar.output import Hdf5OutputMethod
from lascar.session import Session
from lascar.tools.leakage_model import hamming

from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# parse hamming weight or hamming distance
parser = argparse.ArgumentParser(description="TOFU")
parser.add_argument("-s", "--settings", type=str, help="path to settings.json", required=False)
namespace = parser.parse_args()
if namespace.settings is not None:
    settings_file = namespace.settings
print("settings file: %s" % settings_file)

with open(settings_file) as f:
    settings = json.load(f)

leakage_model = settings["leakageModel"]

if leakage_model not in ["HammingWeight", "HammingDistance"]:
    raise Exception("undefined leakage model: %s" % leakage_model)

fileName = "traces.h5"

container = Hdf5Container(fileName)


guess_range = range(256)

if leakage_model == "HammingWeight":

    def generate_selection_function(byte):
        # only encrypt
        # hw leakage is then hw(sbox[plain + key])
        def selection_with_guess(value, guess):
            return hamming(sbox[value[byte] ^ guess])

        return selection_with_guess

else:

    def generate_selection_function(byte):
        # only encrypt
        # 0xUU is converted into integer and thus into 0x00 during the VCD simulation, which is then substituted by the s-box
        # hd leakage is then hw(sbox[0] ^ sbox[plain + key])
        initial_register_value = 0x00

        def selection_with_guess(value, guess):
            return hamming(sbox[initial_register_value] ^ sbox[value[byte] ^ guess])

        return selection_with_guess


cpa_engines = [
    CpaEngine(
        generate_selection_function(i),
        guess_range,
    )
    for i in range(16)
]


hdf5_output_method = Hdf5OutputMethod("correlation.h5", *cpa_engines)

session = Session(
    container,
    engines=cpa_engines,
    name="cpa on 16 bytes",
    # output_method=ScoreProgressionOutputMethod(*cpa_engines),
    # output_method=hdf5_output_method,
    output_steps=10,
)

session.run(batch_size=1000)


key = np.ones((16,), np.uint8) * -1

with PdfPages("correlation.pdf") as pdf:
    for i in range(16):
        results = cpa_engines[i].finalize()
        results = np.abs(results)
        correlation = results.max(1)
        key[i] = results.max(1).argmax()
        print(" ".join(format(x, "02x") for x in key))

        sample = results.max(0).argmax()

        plt.figure()
        plt.plot(correlation)
        plt.title("KeyByte %d" % i)
        plt.xlim(xmin=0, xmax=255)
        plt.ylim(ymin=0, ymax=1)
        plt.xlabel("KeyByteVal = %d, MEAN = %.4f, MAX = %.4f, at Sample: %d" % (key[i], np.mean(correlation), np.max(correlation), sample))
        plt.ylabel("Correlation")
        plt.grid()
        pdf.savefig()
        plt.close()
