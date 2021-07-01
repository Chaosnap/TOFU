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
        // Only contains signals under inspection.
        VariableState var_state_;

        // Current position within the file.
        char* file_pointer_;

        // End of file
        const char* file_end_;

        // Collects leakage information (either Hamming Distance or Hamming Weight).
        std::vector<int64_t> leakage_;

        // Collects the extraced value (same order as in file)
        std::vector<char*> extracted_values_;

        void ParseHeader(std::set<std::string>* inspected_signals, std::set<std::string>* var_definitions);
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