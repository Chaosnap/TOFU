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

import binascii
import unicorn
import re
import sys

VERBOSE = False

# load memory image
with open("aes-c/main.bin", "rb") as fid:
    THUMB_CODE = fid.read()

file_tv = sys.argv[1]
file_vcd = sys.argv[2]

with open(file_tv) as fid:
    tv = fid.read()

match = re.match(r"^([0-9a-f]{32}) ([0-9a-f]{32})$", tv)
if match is not None:
    plain = match.groups()[0]
    key = match.groups()[1]
else:
    raise Exception()

plain = binascii.unhexlify(plain)
key = binascii.unhexlify(key)

# print(tv)
# print("-" * 10)
# print(file_tv, file_vcd)
# print(plain, key)


# code to be emulated
# THUMB_CODE = b"\x83\xb0\x83\xb0\x83\xb0"  # sub    sp, #0xc

ROM_ADDRESS = 0x08000000
ROM_SIZE = 256 * 1024
RAM_ADDRESS = 0x20000000
RAM_SIZE = 16 * 1024
PERIPHERAL_ADDRESS = 0x40000000
PERIPHERAL_SIZE = 1024
peripheral_memory_init = plain + key + b"\x00" * (PERIPHERAL_SIZE - len(plain) - len(key))

RAM_CHUNK_SIZE = 512
RAM_CHUNK_NUMBER = (RAM_SIZE * 8) // RAM_CHUNK_SIZE
RAM_CHUNK_ITERATOR = range(RAM_CHUNK_NUMBER)
RAM_CHUNK_ITERATOR = [0, 1, 2, 253, 254, 255]

signal_width = {
    "R0": 32,
    "R1": 32,
    "R2": 32,
    "R3": 32,
    "R4": 32,
    "R5": 32,
    "R6": 32,
    "R7": 32,
    "R8": 32,
    "R9": 32,
    "R10": 32,
    "R11": 32,
    "R12": 32,
    "SP": 32,
    "LR": 32,
    "PC": 32,
    "tick": 32,
    "peripheral": 2 * 128,
}

for i in RAM_CHUNK_ITERATOR:
    signal_width[f"ram_{i}"] = RAM_CHUNK_SIZE


def get_emulator_state(uc):
    state = dict()
    state["R0"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R0)
    state["R1"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R1)
    state["R2"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R2)
    state["R3"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R3)
    state["R4"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R4)
    state["R5"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R5)
    state["R6"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R6)
    state["R7"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R7)
    state["R8"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R8)
    state["R9"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R9)
    state["R10"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R10)
    state["R11"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R11)
    state["R12"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_R12)
    state["SP"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_SP)
    state["LR"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_LR)
    state["PC"] = uc.reg_read(unicorn.arm_const.UC_ARM_REG_PC)
    state["tick"] = uc.tick
    state["peripheral"] = int.from_bytes(uc.mem_read(PERIPHERAL_ADDRESS, 16 * 2), "big")

    ram = uc.mem_read(RAM_ADDRESS, RAM_SIZE)
    for i in RAM_CHUNK_ITERATOR:
        x = (i + 0) * RAM_CHUNK_SIZE // 8
        y = (i + 1) * RAM_CHUNK_SIZE // 8
        state[f"ram_{i}"] = int.from_bytes(ram[x:y], "big")

    return state


def padhexprint(x, bits):
    return "0x" + hex(x)[2:].rjust(bits // 8 * 2, "0")


# callback for tracing basic blocks
def hook_block(uc, address, size, user_data):
    if VERBOSE:
        print("-" * 100)
        print(">>> BASIC BLOCK at 0x%x, block size = 0x%x" % (address, size))


# callback for tracing instructions
def hook_code(uc, address, size, user_data):
    state = get_emulator_state(uc)
    instruction = uc.mem_read(address, size)
    str_instruction = re.sub(b"(.)(.)", r"\2\1", instruction)
    str_instruction = str(binascii.hexlify(str_instruction))[2:-1]
    str_address = hex(address)
    str_size = hex(size)

    if VERBOSE:
        print("-" * 100)
        print(f">>> INSTRUCTION {str_instruction} at {str_address} size = {str_size} tick {mu.tick}")

    if uc.capture_full_trace:
        uc.trace.append(state)

    changes = dict()
    for key in state.keys():
        if state[key] != uc.last_state[key]:
            changes[key] = state[key]

    if VERBOSE:
        change_string = "\n".join([f">>> {i}: {padhexprint(changes[i],signal_width[i])}" for i in changes.keys()])
        print(change_string)

    if changes:
        uc.change_trace.append(changes.copy())
    uc.last_state = state

    if address == ROM_ADDRESS + 4:
        uc.emu_stop()
    else:
        uc.tick += 1


# callback for tracing memory access (READ or WRITE)
def hook_mem_access(uc, access, address, size, value, user_data):
    # print("-" * 100)
    if access == unicorn.UC_MEM_WRITE:
        value = value.to_bytes(size, "little")
        value = str(binascii.hexlify(value))[2:-1]
        if VERBOSE:
            print(f">>> MEM WRITE at {hex(address)}, size = {hex(size)}, value = {value}")
    elif access == unicorn.UC_MEM_READ:
        value = uc.mem_read(address, size)
        value = str(binascii.hexlify(value))[2:-1]
        if VERBOSE:
            print(f">>> MEM READ at {hex(address)}, size = {hex(size)}, value = {value}")
    else:
        raise Exception()


# initialize emulator in thumb mode
mu = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_THUMB)

# map memory of emulator rom ram peripheral
mu.mem_map(ROM_ADDRESS, ROM_SIZE)
mu.mem_map(RAM_ADDRESS, RAM_SIZE)
mu.mem_map(PERIPHERAL_ADDRESS, PERIPHERAL_SIZE)

# write machine code to be emulated to memory
mu.mem_write(ROM_ADDRESS, THUMB_CODE)
mu.mem_write(RAM_ADDRESS, b"\x00" * RAM_SIZE)
mu.mem_write(PERIPHERAL_ADDRESS, b"\x00" * PERIPHERAL_SIZE)
mu.mem_write(PERIPHERAL_ADDRESS, peripheral_memory_init)

# initialize machine registers
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R0, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R1, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R2, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R3, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R4, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R5, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R6, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R7, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R8, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R9, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R10, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R11, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_R12, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_SP, RAM_ADDRESS + RAM_SIZE)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_LR, 0)
mu.reg_write(unicorn.arm_const.UC_ARM_REG_PC, ROM_ADDRESS)

# tracing with customized callbacks
mu.hook_add(unicorn.UC_HOOK_CODE, hook_code)
mu.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_mem_access)
mu.hook_add(unicorn.UC_HOOK_MEM_READ, hook_mem_access)
mu.hook_add(unicorn.UC_HOOK_BLOCK, hook_block)

# prepare instruction trace
mu.trace = list()
mu.tick = 0

# capture a full trace of every register
mu.capture_full_trace = False

# capture change trace
mu.last_state = get_emulator_state(mu)
mu.change_trace = list()
mu.change_trace.append(get_emulator_state(mu))

if mu.capture_full_trace:
    mu.trace.append(get_emulator_state(mu))

mu.tick += 1

# emulate machine code in infinite time
# note we start at ROM_ADDRESS | 1 to indicate THUMB mode.
mu.emu_start(ROM_ADDRESS | 1, ROM_ADDRESS + len(THUMB_CODE))

if VERBOSE:
    print("-" * 100)
    print(">>> emulation is done")

change_trace = mu.change_trace

if mu.capture_full_trace:
    trace = mu.trace

    # check if change trace is correct
    recovered_trace = list()
    recovered_state = change_trace[0].copy()
    recovered_trace.append(recovered_state.copy())
    for i in mu.change_trace[1:]:
        for key in i.keys():
            recovered_state[key] = i[key]
        recovered_trace.append(recovered_state.copy())

    assert trace == recovered_trace

# generate vcd file
identifiers = dict()
for i, key in enumerate(change_trace[0].keys()):
    identifiers[key] = hex(i)[2:]

date = "somedate"
version = "someversion"
comment = "somecomment"
register = "\n".join([f"$var wire {signal_width[i]} {identifiers[i]} {i} $end" for i in change_trace[0].keys()])
dumpvars = ""
updates = ""

for key in change_trace[0].keys():
    dumpvars += f"b{bin(change_trace[0][key])[2:]} {identifiers[key]}\n"
dumpvars = dumpvars[:-1]

for c in change_trace[1:]:
    tick = c["tick"]
    updates += f"#{tick}" + "\n"
    for key in c.keys():
        updates += f"b{bin(c[key])[2:]} {identifiers[key]}\n"
updates = updates[:-1]

vcd_string = f"""$date
{date}
$end
$version
{version}
$end
$timescale
1s
$end
$comment
{comment}
$end
$scope module register $end
{register}
$upscope $end
$enddefinitions $end
#0
$dumpvars
{dumpvars}
$end
{updates}
"""

with open(file_vcd, "w") as fid:
    fid.write(vcd_string)
