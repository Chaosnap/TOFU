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

import numpy as np
import logging


def valueExtractPlaintext(self):
    # create a logger
    logger = logging.getLogger("synthesize")
    logger.info("extracting value (plaintext)")

    value_signal_numeric_id = 2
    value_signal_time_from = 0

    foo = None
    # if value_signal_numeric_id not in self.numeric_ids_under_inspection_set:
    #     raise Exception("signal %s is not in the loaded pickle" % value_signal_numeric_id)

    for update in self.updates:
        if update[0] == value_signal_time_from and update[1] == value_signal_numeric_id:
            plain = bin(update[2])[2:].rjust(128, "0")
            foo = int(plain, 2).to_bytes(-(-len(plain) // 8), byteorder="big")
            foo = list(foo)
            break

    if foo is None:
        raise Exception()

    # print(update)
    # print(plain)

    value = np.array(foo, dtype=np.uint8)

    return value
