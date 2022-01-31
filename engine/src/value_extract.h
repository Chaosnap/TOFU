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

#ifndef VALUE_EXTRACT_H_
#define VALUE_EXTRACT_H_
#include <vector>

#include "variable_state.h"

struct ValueExtract {
    int64_t time;
    std::vector<IdentifierCode> ids;
    size_t index;
};

#endif // VALUE_EXTRACT_H_