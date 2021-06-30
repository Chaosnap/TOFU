#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: parse.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de, Florian Kasten
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
from lascar.tools.aes import sbox
from lascar.container import Hdf5Container
from lascar.engine import CpaEngine
from lascar.output import Hdf5OutputMethod
from lascar.session import Session
from lascar.tools.leakage_model import hamming

from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

fileName = "traces.h5"

container = Hdf5Container(fileName)


guess_range = range(256)


def generate_selection_function(byte):
    # only encrypt
    def selection_with_guess(value, guess):
        return hamming(sbox[value[byte] ^ guess])

    return selection_with_guess


cpa_engines = [
    CpaEngine(
        "byte_%02d" % i,
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
