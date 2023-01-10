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

# main file variables
FILE:=main

STARTUP_SOURCES:=startup.s
LINKER_SCRIPT:=linker.ld

C_FLAGS:=-Wall -nostartfiles -O0 -ffreestanding -mcpu=cortex-m4 -mthumb -fdata-sections -ffunction-sections
AS_FLAGS:=--warn --fatal-warnings -mcpu=cortex-m4
LD_FLAGS:=--nostdlib --gc-sections #--no-warn-rwx-segment

C_SOURCES:=$(wildcard *.c)
AS_SOURCES:=$(wildcard *.s)
AS_SOURCES:=$(filter-out $(AS_SOURCES), startup.s)
OBJECTS:=$(STARTUP_SOURCES:.s=.o) $(AS_SOURCES:.s=.o) $(C_SOURCES:.c=.o)

MAIN_SUFFIXES:=.elf .bin .dump .hex .lst
MAIN_TARGETS:= $(foreach suffix,$(MAIN_SUFFIXES),$(addsuffix $(suffix),$(FILE)))

all: $(MAIN_TARGETS)

clean:
	rm -f $(OBJECTS)
	rm -f $(MAIN_TARGETS)
	rm -f aes.out

%.o : %.c
	arm-none-eabi-gcc $(C_FLAGS) -c $< -o $@

%.o : %.s
	arm-none-eabi-as $(AS_FLAGS) $< -o $@

$(FILE).elf : $(OBJECTS)
	arm-none-eabi-ld $(LD_FLAGS) -T $(LINKER_SCRIPT) $(OBJECTS) -o $(FILE).elf

$(FILE).bin : $(FILE).elf
	arm-none-eabi-objcopy -O binary $(FILE).elf $(FILE).bin

$(FILE).dump : $(FILE).bin
	xxd $(FILE).bin > $(FILE).dump

$(FILE).hex : $(FILE).elf
	arm-none-eabi-objcopy -O ihex $(FILE).elf $(FILE).hex

$(FILE).lst : $(FILE).elf
	arm-none-eabi-objdump -D $(FILE).elf > $(FILE).lst

test : aes.out
	./aes.out

aes.out : aes.c
	gcc -DAES_TEST_MODE $< -o $@

.PHONY: all simulate clean