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

import sys
import random
import binascii

key = binascii.hexlify(bytearray([i for i in range(100, 116)])).decode("ascii")
# key = "2b7e151628aed2a6abf7158809cf4f3c"


file_name = sys.argv[1]
index = int(sys.argv[2])

# # ensure same plaintext on every run
# random.seed(a=index)
# # warmup
# random.randbytes(10000)


def get_random_plaintext():
    return "%032x" % random.randrange(16**32)


# AES-VHDL expects plaintext and key to be in little-endian.
# The ciphertext is also returned in little-endian.
# This function can be used to convert between BE <-> LE
def reverse_byte_order(a):
    ba = bytearray.fromhex(a)
    ba.reverse()
    return "".join(format(x, "02x") for x in ba)


with open(file_name, "w") as f:
    f.write(get_random_plaintext())
    f.write(" ")
    f.write(key)


# if use_test_vectors:
#     # TVLA (Test 0): https://csrc.nist.gov/csrc/media/events/non-invasive-attack-testing-workshop/documents/08_goodwill.pdf
#     from Crypto.Cipher import AES

#     if nr_simulations % 2 != 0:
#         nr_simulations += 1
#     nr_simulations //= 2
#     key = "0123456789abcdef123456789abcedf0"
#     plaintext = "0" * 32
#     cipher = AES.new(bytes.fromhex(key), AES.MODE_ECB)

#     # dataset 1
#     for i in range(1, nr_simulations + 1):
#         with open(testbench_name + str(i), "w") as f:
#             f.write(reverse_byte_order(plaintext))
#             f.write("\n")
#             f.write(reverse_byte_order(key))
#         plaintext = cipher.encrypt(bytes.fromhex(plaintext)).hex()

#     # dataset 2
#     plaintext = "da39a3ee5e6b4b0d3255bfef95601890"
#     for i in range(nr_simulations + 1, 2 * nr_simulations + 1):
#         with open(testbench_name + str(i), "w") as f:
#             f.write(reverse_byte_order(plaintext))
#             f.write("\n")
#             f.write(reverse_byte_order(key))

# else:
#     # fixed key, random plaintexts
#     key = "2b7e151628aed2a6abf7158809cf4f3c"
#     for i in range(1, nr_simulations + 1):
#         with open(testbench_name + str(i), "w") as f:
#             f.write(get_random_plaintext())
#             f.write("\n")
#             f.write(key)
