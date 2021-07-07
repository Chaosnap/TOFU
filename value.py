#!/usr/bin/python3
# -*- coding: utf-8 -*-
# TOFU: value.py
# -------------------------------------------------------------------------------------------------
# Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
# All Rights Reserved.
# For internal use only.
# -------------------------------------------------------------------------------------------------
# Author: Michael Gruber m.gruber@tum.de
# Date:   18.05.2020
# -------------------------------------------------------------------------------------------------

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
            plain = update[2]
            foo = int(plain, 2).to_bytes(-(-len(plain) // 8), byteorder="big")
            foo = list(foo)
            break
    if foo is None:
        raise Exception()

    # print(update)
    # print(plain)

    value = np.array(foo, dtype=np.uint8)

    return value


def valueExtractIndex(self):
    # create a logger
    logger = logging.getLogger("synthesize")
    logger.info("extracting value (key) i.e. index: %d" % (self.index))
    return np.array([[self.index]], dtype=np.uint8)
