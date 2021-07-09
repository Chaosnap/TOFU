BUILD_DIR=build
CXX=g++
SZ = size

CPP_SOURCES := $(wildcard src/*.cc)
OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(CPP_SOURCES:.cc=.o)))
vpath %.cc $(sort $(dir $(CPP_SOURCES)))

INSPECTED_SIGNALS_FILENAME?="../example-aes-vhdl/signals_name.json"
VALUE_EXTRACT_FILE?="../example-aes-vhdl/ntofu_values_to_extract.val"
VCD_GLOB?="../example-aes-vhdl/vcd/aes*.vcd"

# this needs to be set before running the makefile, for example: 'make run DEBUG=1'
ifeq ($(DEBUG), 1)
	CXX_DEFS += -DDEBUG -Og -g -DINSPECTED_SIGNALS_FILENAME=$(INSPECTED_SIGNALS_FILENAME) -DVALUE_EXTRACT_FILE=$(VALUE_EXTRACT_FILE) -DVCD_GLOB=$(VCD_GLOB)
	TARGET=$(BUILD_DIR)/standalone_parser
	LDFLAGS:=-W -Wall -Og -flto -g  
else
	CXX_DEFS += -O3
	TARGET=$(BUILD_DIR)/library.so
	LDFLAGS:=-W -Wall -O3 -flto -shared
endif

CXXFLAGS=-Wall -Wpedantic -std=c++17 $(CXX_DEFS) -c -fPIC -flto
CXXFLAGS+= -MMD -MP -MF"$(@:%.o=%.d)"

all: $(TARGET)

run: all vcds
	./$(TARGET)

debug: $(TARGET) vcds
	gdb -tui $(TARGET)
	
vcds:
	make -C ../example-aes-vhdl simulate NR_SIMULATIONS=10

$(BUILD_DIR)/%.o: %.cc Makefile | $(BUILD_DIR)
	$(CXX) -c $(CXXFLAGS) $< -o $@

$(TARGET): $(OBJECTS) Makefile
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR):
	mkdir $@		

clean:
	rm -rf $(BUILD_DIR)