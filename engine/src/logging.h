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
// Written by the following authors: Florian Kasten, Michael Gruber

#ifndef LOGGING_H
#define LOGGING_H
#include <iostream>

#define FATAL(msg)                                                                                         \
    do {                                                                                                   \
        std::cerr << "Fatal error in " << __FILE__ << " on line " << __LINE__ << ". " << msg << std::endl; \
        abort();                                                                                           \
    } while (0)

#define CHECK(condition)                           \
    do {                                           \
        if (!(condition)) {                        \
            FATAL("Check failed: " << #condition); \
        }                                          \
    } while (0)

#ifdef DEBUG
#define DCHECK(condition)    CHECK(condition)
#else
#define DCHECK(condition) do {} while(0)
#endif

#define UNREACHABLE()    FATAL("Unreachable");

#define UNIMPLEMENTED()    FATAL("Unimplemented");

#endif //LOGGING_H