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

#include "parser.h"

#include <string.h>
#include <sys/mman.h>

#include <set>
#include <iostream>
#include <vector>
#include <algorithm>

#include "logging.h"
#include "file_mem_map.h"
#include "value_extract.h"

Parser::Parser(const char *file_name, std::set<std::string> *inspected_signals, LeakageModel leakage_model,
               bool align, uint64_t downsample, std::set<std::string> *var_definitions,
               std::vector<ValueExtract *> *values_to_extract)
    : extracted_values_(values_to_extract->size(), 0)
{
    size_t file_length;
    const char *file_start = MapFile(file_name, file_length);
    file_end_ = file_start + file_length;
    file_pointer_ = const_cast<char *>(file_start);

    // Collect all IDs which should be extracted
    std::vector<IdentifierCode> ids_to_extract;
    for (auto ve : *values_to_extract) {
        for (auto id : ve->ids) {
            ids_to_extract.push_back(id);
        }
    }

    // Preallocate memory to avoid reallocations.
    leakage_.reserve(file_length / 100);

    // VCD File ::= { declaration_command } { simulation_command }
    ParseHeader(inspected_signals, var_definitions, &ids_to_extract);
    ParseValueChangeSection(leakage_model, align, downsample, values_to_extract);
    CHECK(munmap(const_cast<void *>(static_cast<const void *>(file_start)), file_length) != -1);
}

int64_t *Parser::GetLeakage(size_t *length)
{
    *length = leakage_.size();
    int64_t *ret = static_cast<int64_t *>(malloc(*length * sizeof(int64_t)));
    memcpy(ret, &leakage_[0], *length * sizeof(int64_t));
    return ret;
}

char **Parser::GetExtractedValues()
{
    // deep copy extracted values
    char **ret = static_cast<char **>(malloc(extracted_values_.size() * sizeof(char *)));
    for (size_t i = 0; i < extracted_values_.size(); i++)
    {
        ret[i] = extracted_values_[i]; // extracted_values_[i] will not get freed with the Parser object
    }
    return ret;
}

IdentifierCode Parser::ReadIdentifierCode(const char *start, size_t length)
{
    if (length <= 8)
    {
        u_int64_t identifier_code_fast = 0;
        memcpy(&identifier_code_fast, start, length);
        return identifier_code_fast;
    }
    else
    {
        return std::string(start, length);
    }
}

void Parser::ParseHeader(std::set<std::string> *inspected_signals, std::set<std::string> *var_definitions, 
                         std::vector<IdentifierCode> *ids_to_extract)
{
    bool should_filter_signals = !inspected_signals->empty();
    std::string current_scope = "";
    bool should_insert_var_defs = var_definitions->empty();

    // declaration_command ::= "$var" [ var_type size identifier_code reference ] "$end"
    //                       | "$scope" [ scope_type scope_identifier ] "$end"
    //                       | "$upscope $end"
    //                       | "$enddefinitions $end"
    //                       | "$date" [ date_text ] "$end"
    //                       | "$version" [ version_text system_task ] "$end"
    //                       | "$timescale" [ time_number time_unit ] "$end"
    //                       | "$comment" [ comment_text ] "$end"
    while (true)
    {
        if (Parse("$var "))
        {
            // "$var" var_type size identifier_code reference "$end"
            char *file_pointer_start = file_pointer_;

            // parse var_type
            char *var_type = ParseUntil(" ");
            free(var_type);
            ++file_pointer_;

            // parse size
            const unsigned long size = strtoul(file_pointer_, &file_pointer_, 10);
            ++file_pointer_;

            // parse identifier_code
            const size_t string_length = CharsUntil(" ");
            IdentifierCode identifier_code = ReadIdentifierCode(file_pointer_, string_length);
            file_pointer_ += string_length + 1;

            // parse reference
            if (should_filter_signals)
            {
                size_t reference_size = CharsUntil(" $end");
                std::string reference = std::string(file_pointer_, reference_size);

                // check if either the whole module should be inspected or this specific variable
                if (inspected_signals->find(current_scope) != inspected_signals->end() ||
                    inspected_signals->find(current_scope + "->" + reference) != inspected_signals->end())
                {
                    var_state_.insert(identifier_code, size);
                }
                else if (std::find(ids_to_extract->begin(), ids_to_extract->end(), identifier_code) != ids_to_extract->end()) {
                    ids_to_extract_not_filter_.push_back(identifier_code);
                    var_state_.insert(identifier_code, size);
                }
            }
            else
            {
                var_state_.insert(identifier_code, size);
            }

            file_pointer_ += CharsUntil("\n") + 1;

            // if parsing multiple files: make sure that this variable exists in all files
            file_pointer_ = file_pointer_start;
            char *var_info = ParseUntil(" $end");
            std::string var_info_str(var_info);
            free(var_info);
            if (should_insert_var_defs)
                var_definitions->insert(var_info_str);
            else
                CHECK(var_definitions->find(var_info_str) != var_definitions->end());

            ParseUntilEnd();
        }
        else if (Parse("$scope "))
        {
            // $scope" [ scope_type scope_identifier] "$end
            if (should_filter_signals)
            {
                const size_t length = CharsUntil(" $end");
                if (current_scope.length() > 0)
                    current_scope += "->" + std::string(file_pointer_, length);
                else
                    current_scope += std::string(file_pointer_, length);
            }
            ParseUntilEnd();
        }
        else if (Parse("$upscope $end\n"))
        {
            if (should_filter_signals)
            {
                size_t pos = current_scope.rfind("->");
                current_scope.erase(pos == std::string::npos ? 0 : pos);
            }
        }
        else if (Parse("$enddefinitions $end\n"))
            break;
        else if (Parse("$date"))
            ParseUntilEnd();
        else if (Parse("$version"))
            ParseUntilEnd();
        else if (Parse("$timescale"))
            ParseUntilEnd();
        else if (Parse("$comment"))
            ParseUntilEnd();
        else if (Parse("\n"))
            continue;
        else
            UNREACHABLE();
    }
}

// Parses { simulation_command }.
void Parser::ParseValueChangeSection(LeakageModel leakage_model, bool align, uint64_t downsample,
                                     std::vector<ValueExtract *> *values_to_extract)
{
    // simulation_command ::= "$dumpall" { value_change } "$end"
    //                      | "$dumpoff" { value_change } "$end"
    //                      | "$dumpon" { value_change } "$end"
    //                      | "$dumpvars" { value_change } "$end"
    //                      | "$comment" [ comment_text ] "$end"
    //                      | simulation_time
    //                      | value_change
    CHECK(downsample != 0);
    int64_t current_leakage = 0;
    int64_t last_index = -1; // for align
    int64_t last_simulation_time = -1;
    auto current_value_extract = values_to_extract->begin();

    // make sure that identifiers specified for value extract exist
    for (auto ve : *values_to_extract)
    {
        for (IdentifierCode id : ve->ids)
        {
            CHECK(var_state_.contains(id));
        }
    }

    // sort value_extract by time (<)
    std::sort(values_to_extract->begin(), values_to_extract->end(), [](auto a, auto b) -> bool
              { return a->time < b->time; });

    auto maybe_add_extracted_values = [&]()
    {
        while (current_value_extract != values_to_extract->end() &&
               (*current_value_extract)->time <= last_simulation_time)
        {
            char *value_bit_string = this->var_state_.get_bit_string((*current_value_extract)->ids);
            extracted_values_[(*current_value_extract)->index] = value_bit_string;
            current_value_extract++;
        }
    };

    while (file_pointer_ < file_end_)
    {
        if (Parse("#"))
        {
            // simulation_time ::= "#" decimal_number

            // Parse + Insert into leakage_
            const long simulation_time = strtol(file_pointer_, NULL, 10);
            if (align)
            {
                const long new_index = simulation_time / downsample;
                if (new_index > last_index + 1)
                { // will only occur if: len of leakage > number of updates
                    leakage_.insert(leakage_.end(), new_index - last_index - 1, current_leakage);
                }
                if (new_index != last_index)
                {
                    leakage_.push_back(current_leakage);
                    if (leakage_model == HammingDistance)
                    {
                        current_leakage = 0;
                    }
                    last_index = new_index;
                }
            }
            else
            {
                leakage_.push_back(current_leakage);
                if (leakage_model == HammingDistance)
                {
                    current_leakage = 0;
                }
            }

            // Value extract
            maybe_add_extracted_values();
            last_simulation_time = simulation_time;

            file_pointer_ += CharsUntil("\n") + 1;
        }
        else if (Parse("$dumpvars\n") || Parse("$end\n"))
        {
            // Skip.
        }
        else if (Parse("$dumpall"))
        {
            UNIMPLEMENTED();
        }
        else if (Parse("$dumpoff"))
        {
            UNIMPLEMENTED();
        }
        else if (Parse("$dumpon"))
        {
            UNIMPLEMENTED();
        }
        else if (Parse("$comment"))
        {
            UNIMPLEMENTED();
        }
        else
        {
            // value_change ::= scalar_value_change | vector_value_change
            const char first_char = *file_pointer_++;
            const bool is_scalar_0 = first_char == '0' || first_char == 'x' || first_char == 'X' || first_char == 'z' || first_char == 'Z'; // every value despite 1 is interpreted as 0
            const bool is_scalar_1 = first_char == '1';
            if (is_scalar_0 || is_scalar_1)
            {
                // scalar_value_change ::= value identifier_code
                //
                // value ::= "0" | "1" | "x" | "X" | "z" | "Z"
                //
                // identifier_code ::= { ASCII character}
                const size_t string_length = CharsUntil("\n");
                IdentifierCode identifier_code = ReadIdentifierCode(file_pointer_, string_length);
                file_pointer_ += string_length;
                if (!var_state_.contains(identifier_code))
                {
                    file_pointer_ += CharsUntil("\n") + 1;
                    continue;
                }

                DCHECK(var_state_.var_size(identifier_code) == 1);

                if (std::find(ids_to_extract_not_filter_.begin(), ids_to_extract_not_filter_.end(), identifier_code) == ids_to_extract_not_filter_.end()) {
                    switch (leakage_model)
                    {
                    case HammingDistance:
                        current_leakage += var_state_.get(identifier_code, 0) ^ is_scalar_1;
                        break;
                    case HammingWeight:
                        if (var_state_.get(identifier_code, 0) ^ is_scalar_1)
                        {
                            current_leakage += is_scalar_1 ? 1 : -1;
                        }
                        break;
                    }
                    DCHECK(current_leakage >= 0);
                }

                var_state_.set(identifier_code, 0, is_scalar_1);
                file_pointer_ += 1; // skip newline
            }
            else if (first_char == 'b' || first_char == 'B')
            {
                // vector_value_change ::= "b" binary_number identifier_code
                //                       | "B" binary_number identifier_code
                //                       | ...
                //
                // binary_number ::= {"0" | "1" | "x" | "z"}
                const int nr_of_bits = CharsUntil(" ");
                const int string_length = CharsUntil("\n") - nr_of_bits - 1;
                IdentifierCode identifier_code = ReadIdentifierCode(file_pointer_ + nr_of_bits + 1, string_length);
                if (!var_state_.contains(identifier_code))
                {
                    file_pointer_ += CharsUntil("\n") + 1;
                    continue;
                }

                DCHECK(nr_of_bits <= (int)var_state_.var_size(identifier_code));
                for (int i = var_state_.var_size(identifier_code) - 1; i >= 0; i--)
                {
                    const char currentChar = i >= nr_of_bits ? '0' : *file_pointer_++; // ljust with 0 if necessary
                    // if (currentChar == 'U')
                    //     continue;
                    // every value despite 1 is interpreted as 0
                    DCHECK(currentChar == '0' ||
                           currentChar == '1' ||
                           currentChar == 'x' ||
                           currentChar == 'X' ||
                           currentChar == 'u' ||
                           currentChar == 'U' ||
                           currentChar == 'z' ||
                           currentChar == 'Z');

                    if (std::find(ids_to_extract_not_filter_.begin(), ids_to_extract_not_filter_.end(), identifier_code) == ids_to_extract_not_filter_.end()) {
                        switch (leakage_model)
                        {
                        case HammingDistance:
                            current_leakage += var_state_.get(identifier_code, i) ^ (currentChar == '1');
                            break;
                        case HammingWeight:
                            if (var_state_.get(identifier_code, i) ^ (currentChar == '1'))
                            {
                                current_leakage += (currentChar == '1') ? 1 : -1;
                            }
                            break;
                        }
                    }
                    
                    DCHECK(current_leakage >= 0);
                    var_state_.set(identifier_code, i, currentChar == '1');
                }
                file_pointer_ += 2 + string_length; // skip whitespace + identifier_code + newline
            }
            else if (first_char == 'r' || first_char == 'R')
            {
                UNIMPLEMENTED();
            }
            else
            {
                UNREACHABLE();
            }
        }
    }

    // Value extract for last timestamp
    maybe_add_extracted_values();

    // check if all values to be extracted are found
    CHECK(current_value_extract == values_to_extract->end());

    if (!align)
    {
        leakage_.push_back(current_leakage);
    }

    if (leakage_.size() >= 1)
        leakage_.erase(leakage_.begin());

    if (leakage_model == HammingDistance)
    {
        if (leakage_.size() >= 1)
            leakage_.erase(leakage_.begin());
    }
}

inline bool Parser::Parse(const char *keyword)
{
    const size_t length = strlen(keyword);
    if (strncmp(file_pointer_, keyword, length) == 0)
    {
        file_pointer_ += length;
        return true;
    }
    return false;
}

inline char *Parser::ParseUntil(const char *find)
{
    const size_t size = CharsUntil(find);
    char *copy = static_cast<char *>(malloc(size + 1));
    strncpy(copy, file_pointer_, size);
    copy[size] = '\0';
    file_pointer_ += size;
    return copy;
}

inline void Parser::ParseUntilEnd()
{
    constexpr char kEnd[] = "$end\n";
    free(ParseUntil(kEnd));
    file_pointer_ += strlen(kEnd);
}

inline size_t Parser::CharsUntil(const char *find) const
{
    const char *ret = strstr(file_pointer_, find);
    DCHECK(ret != NULL);
    return ret - file_pointer_;
}