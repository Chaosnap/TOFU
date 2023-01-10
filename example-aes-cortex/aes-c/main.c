// This file is part of TOFU
//
// TOFU is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// Copyright 2022 (C)
// Technical University of Munich
// TUM Department of Electrical and Computer Engineering
// Chair of Security in Information Technology
// Written by the following authors: Michael Gruber

#include <stdint.h>

#define PERIPHERAL_ADDRESS 0x40000000

void aes128_init(uint8_t *key);
void aes128_encrypt(uint8_t *buffer);

#define TEST

void main(void)
{
    uint8_t *aes_buffer = (uint8_t *)(PERIPHERAL_ADDRESS + 0);
    uint8_t *aes_key = (uint8_t *)(PERIPHERAL_ADDRESS + 16);
    aes128_init(aes_key);
    aes128_encrypt(aes_buffer);
}