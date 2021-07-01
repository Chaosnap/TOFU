#ifndef VARIABLE_STATE_H_
#define VARIABLE_STATE_H_
#include <vector>
#include <unordered_map>
#include <string>
#include <variant>

typedef std::variant<uint64_t, std::string> IdentifierCode;

// Keeps track of the current values of variables inside the Parser.
// Uses two maps because:
// - identifiers can be any string but using a string map for all identifiers is too expensive
// - in most cases the identifier is less than 8 bytes and can be represented as an uint64_t
// - using uint64_t instead of strings increases overall performance by a lot
class VariableState {
    private: 
        std::unordered_map<u_int64_t, std::vector<bool>> var_state_fast_;
        std::unordered_map<std::string, std::vector<bool>> var_state_slow_;

    public:
        void insert(IdentifierCode id, size_t size);
        bool get(IdentifierCode id, size_t value_index);
        char* get_bit_string(std::vector<IdentifierCode> ids);
        void set(IdentifierCode id, size_t value_index, bool value);
        size_t var_size(IdentifierCode id);
        bool contains(IdentifierCode id);
};

#endif // VARIABLE_STATE_H_