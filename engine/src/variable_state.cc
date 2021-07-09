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