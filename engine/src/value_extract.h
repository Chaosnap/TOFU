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