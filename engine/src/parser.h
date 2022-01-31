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

#ifndef PARSER_H_
#define PARSER_H_
#include <vector>
#include <map>
#include <set>

#include "variable_state.h"
#include "value_extract.h"

enum LeakageModel { HammingWeight, HammingDistance };

class Parser {
    private:
        // Keeps track of the current value of a variable.
        // Contains signals under inspection and signals to extract.
        VariableState var_state_;

        // Keeps track of all IDs that should be extracted but not used for leakage generation.
        std::vector<IdentifierCode> ids_to_extract_not_filter_;

        // Current position within the file.
        char* file_pointer_;

        // End of file
        const char* file_end_;

        // Collects leakage information (either Hamming Distance or Hamming Weight).
        std::vector<int64_t> leakage_;

        // Collects the extraced value (same order as in file)
        std::vector<char*> extracted_values_;

        void ParseHeader(std::set<std::string>* inspected_signals, std::set<std::string>* var_definitions,
                         std::vector<IdentifierCode>* ids_to_extract);
        void ParseValueChangeSection(LeakageModel leakage_model, bool align, uint64_t downsample, 
                                     std::vector<ValueExtract*>* values_to_extract);
        
        // Tries to read `keyword` starting from file_pointer_ and advances file_pointer_ iff successful.
        inline bool Parse(const char* keyword);

        // Advances file_pointer_ until just before `find`. Returns copy of everything that was parsed.
        inline char* ParseUntil(const char* find);

        // Advances file_pointer_ until after `$end\n`.
        inline void ParseUntilEnd();

        // Returns the number of characters between file_pointer_ and the first occurence of `find`.
        // Does not modify file_pointer_!
        inline size_t CharsUntil(const char* find) const;

    public:
        // Parses the VCD file given by `file_name` and creates the corresponding leakage information given by `leakage_model`.
        // Only considers signals from the file given by `inspected_signals_file_name`.
        // The grammar for a VCD file can be found here: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1620780.
        // Example:
        //    Parser parser("file.vcd", ...);
        //    uint64_t length;
        //    uint64_t* leakage = parser.GetLeakage(&length);
        Parser(const char* file_name, std::set<std::string>* inspected_signals, LeakageModel leakage_model, 
               bool align, uint64_t downsample, std::set<std::string>* var_definitions, 
               std::vector<ValueExtract*>* values_to_extract);

        // Returns a copy of the leakage information and sets `length` accordingly.
        // The caller is responsible for freeing the returned leakage memory.
        int64_t* GetLeakage(size_t* length);

        // Returns a copy of the extracted values.
        // The caller must free the returned memory.
        char** GetExtractedValues();

        // Returns the identifer code starting at `start` of length `length`.
        static IdentifierCode ReadIdentifierCode(const char* start, size_t length);
};

#endif // PARSER_H_