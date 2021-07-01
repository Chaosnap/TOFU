#include <glob.h>
#include <sys/mman.h>

#include <string>
#include <iostream>
#include <thread>
#include <set>
#include <regex>

#include "logging.h"
#include "parser.h"
#include "file_mem_map.h"
#include "variable_state.h"
#include "value_extract.h"

// Properties that are setup by `SetupParser`. Used in `ParseFiles`.
LeakageModel leakage_model_;
std::set<std::string> inspected_signals_;
std::vector<ValueExtract*> values_to_extract_; //time, ids, index
bool align_;
uint64_t downsample_;
std::set<std::string> var_definitions_; // To make sure that all VCDs use the same variables + identifiers.

// To free everything.
size_t last_num_files_ = 0;
int64_t** last_leakages_ = NULL;
size_t* last_leakages_count_ = NULL;
char*** last_extracted_values_ = NULL;
size_t last_extracted_values_count_ = 0;


// Frees everything that gets allocated for the Python code
void FreeAll() {
    if (last_num_files_ == 0)
        return;

    for (int i = 0; i < last_num_files_; ++i) {
        free(last_leakages_[i]);
        for (int j = 0; j < last_extracted_values_count_; ++j) {
            free(last_extracted_values_[i][j]);
        }
    }
    free(last_leakages_);
    free(last_leakages_count_);
    free(last_extracted_values_);
}

// Prepares the parser.
// Must be called before `ParseFiles`.
extern "C" void SetupParser(bool hamming_weight, const char* inspected_signals_file_name, 
                            bool align, uint64_t downsample, const char* value_extract_file) {
    leakage_model_ = hamming_weight ? HammingWeight : HammingDistance;
    align_ = align;
    downsample_ = downsample;

    // If the inspected_signals_file_name is not null, then only the signals and modules in
    // the file should be used for parsing. "->" is used to separate modules and signals.
    // E.g.: "module LWC_TB->module uut->module Inst_Cipher->clk"
    if (inspected_signals_file_name != nullptr) {
        size_t file_length;
        const char* file_start = MapFile(inspected_signals_file_name, file_length);
        std::string file(file_start, file_length);
        std::regex r("\"(.*?)\""); // get everything in between quotation marks
        std::smatch m;
        while (regex_search(file, m, r)) {
            inspected_signals_.insert(m.str(1));
            file = m.suffix();
        }
        CHECK(munmap(const_cast<void*>(static_cast<const void*>(file_start)), file_length) != -1);
    }

    // If the inspected_signals_file_name is not null, this file gives timestamps and ids that should be extracted.
    // Each line in the file must first contain a timestamp, and then at least one id (separated by whitespaces)
    // If a line contains more than one id, the values of those ids are concatenated 
    // Example file:
    // 100 ! 
    // 200 - A
    if (value_extract_file != nullptr) {
        size_t file_length;
        const char* file_start = MapFile(value_extract_file, file_length);
        std::string s(file_start, file_length);
        std::stringstream file_stream(s);
        int i = 0;
        while (file_stream.good()) {
            std::string line;
            std::getline(file_stream, line);
            if (line.size() == 0)
                break;
            std::stringstream line_stream(line);
            std::string time_string;
            std::getline(line_stream, time_string, ' ');
            const long time = std::stoul(time_string, NULL, 0);
            std::vector<IdentifierCode> ids;
            while (line_stream.good()) {
                std::string id_string;
                std::getline(line_stream, id_string, ' ');
                if (id_string.size() == 0)
                    continue;
                IdentifierCode id = Parser::ReadIdentifierCode(id_string.c_str(), id_string.size());
                ids.push_back(id);
            }
            ValueExtract* ve = new ValueExtract;
            ve->time = time;
            ve->ids = ids;
            ve->index = i++;
            values_to_extract_.push_back(ve);
        }
        CHECK(munmap(const_cast<void*>(static_cast<const void*>(file_start)), file_length) != -1);
    }
}

// Parses all files given by `path`. The parser must be setup using `SetupParser` beforehand.
//  
// The following parameters are used as return values: `num_files`, `leakages`, `leakages_count`, `extracted_values` and
// `extracted_values_count`.
extern "C" void ParseFiles(const char* path, size_t* num_files, int64_t*** leakages, size_t** leakages_count, 
                           char**** extracted_values, size_t* extracted_values_count) {
    // Free memory from previous calls to `ParseFiles`
    FreeAll();

    // Collect all VCD Files
    std::vector<std::string> vcd_files;
    glob_t globbuf;
    int glob_ret = glob(path, 0, NULL, &globbuf);
    CHECK(glob_ret == 0);
    for (size_t i = 0; i < globbuf.gl_pathc; ++i) {
        vcd_files.push_back(globbuf.gl_pathv[i]);
    }
    globfree(&globbuf);
    CHECK(vcd_files.size() > 0);
    *num_files = vcd_files.size();
    *extracted_values_count = values_to_extract_.size();

    // Allocate mememory for everything that will be returned
    *leakages = static_cast<int64_t**>(malloc(sizeof(int64_t*) * *num_files));
    *leakages_count = static_cast<size_t*>(malloc(sizeof(size_t) * *num_files));
    *extracted_values = static_cast<char***>(malloc(sizeof(char**) * *num_files));

    // Save references to free later
    last_num_files_ = *num_files;
    last_leakages_ = *leakages;
    last_leakages_count_ = *leakages_count;
    last_extracted_values_ = *extracted_values;
    last_extracted_values_count_ = *extracted_values_count;
    
    // Parse files (TODO: parallelize?)
    for (size_t i = 0; i < *num_files; ++i) {
        Parser parser(vcd_files[i].c_str(), &inspected_signals_, leakage_model_, align_, downsample_,
                      &var_definitions_, &values_to_extract_);
        size_t leakage_length; 
        (*leakages)[i] = parser.GetLeakage(&leakage_length);
        (*leakages_count)[i] = leakage_length;
        (*extracted_values)[i] = parser.GetExtractedValues();
    }
}