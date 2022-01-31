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

#include "variable_state.h"

#include <vector>
#include <algorithm>

void VariableState::insert(IdentifierCode id, size_t size) {
    if (id.index() == 0)
        var_state_fast_.insert(std::make_pair(std::get<0>(id), std::vector<bool>(size, false)));
    else
        var_state_slow_.insert(std::make_pair(std::get<1>(id), std::vector<bool>(size, false)));
}

bool VariableState::get(IdentifierCode id, size_t value_index) {
    if (id.index() == 0)
        return var_state_fast_[std::get<0>(id)][value_index];
    else
        return var_state_slow_[std::get<1>(id)][value_index];
}

char* VariableState::get_bit_string(std::vector<IdentifierCode> ids) {
    std::vector<bool> values;
    for (IdentifierCode id : ids) {
        std::vector<bool> value;
        if (id.index() == 0)
            value = var_state_fast_[std::get<0>(id)];
        else 
            value = var_state_slow_[std::get<1>(id)];
        std::reverse(value.begin(), value.end());
        values.insert(values.end(), value.begin(), value.end());
    }
    char* ret = static_cast<char*>(malloc(values.size() + 1));
    ret[values.size()] = '\0';
    for (size_t i = 0; i < values.size(); ++i) {
        ret[i] = values[i] ? '1' : '0';
    }
    return ret;
}

void VariableState::set(IdentifierCode id, size_t value_index, bool value) {
    if (id.index() == 0)
        var_state_fast_[std::get<0>(id)][value_index] = value;
    else
        var_state_slow_[std::get<1>(id)][value_index] = value;
}

size_t VariableState::var_size(IdentifierCode id) {
    if (id.index() == 0)
        return var_state_fast_[std::get<0>(id)].size();
    else
        return var_state_slow_[std::get<1>(id)].size();
}

bool VariableState::contains(IdentifierCode id) {
    if (id.index() == 0)
        return var_state_fast_.count(std::get<0>(id)) == 1;
    else
        return var_state_slow_.count(std::get<1>(id)) == 1;
}