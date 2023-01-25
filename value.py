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


def valueExtract(self):
    # create a logger
    logger = logging.getLogger("synthesize")
    logger.info("extracting value (key)")

    value_signal_numeric_id = 6776
    value_signal_time_from = 679334500000
    value_signal_time___to = 679350500000

    value_signal_list = []
    value_signal_list_unshared = []

    if value_signal_numeric_id not in self.numeric_ids_under_inspection_set:
        raise Exception("signal %s is not in the loaded pickle" % value_signal_numeric_id)

    # extract key updates
    for update in self.updates:
        if update[0] >= value_signal_time_from and update[0] <= value_signal_time___to and update[1] == value_signal_numeric_id:
            foo = update[2]
            value_signal_list.append(bytearray(int("0b" + foo, 2).to_bytes(4, "big")))
    assert len(value_signal_list) == 16

    # unshare
    for i in range(0, 8):
        x = value_signal_list[i * 2]
        y = value_signal_list[i * 2 + 1]
        assert len(x) == len(y)
        unshared = bytes(x ^ y for (x, y) in zip(x, y))
        value_signal_list_unshared.append(unshared)

    # flatten
    value = [item for sub in value_signal_list_unshared for item in sub]

    assert len(value) == 32
    value = np.array([value], dtype=np.uint8)

    return value


def valueExtractIndex(self):
    # create a logger
    logger = logging.getLogger("synthesize")
    if self.index > np.iinfo(np.uint32).max:
        raise Exception()
    logger.info("extracting value (key) i.e. index: %d" % (self.index))
    return np.array([[self.index]], dtype=np.uint32)
