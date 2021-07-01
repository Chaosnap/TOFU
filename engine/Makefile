OPT=-O3
BUILD_DIR=build
TARGET=$(BUILD_DIR)/library.so

CPP_SOURCES := $(wildcard src/*.cc)

CXX=clang++
 
ifeq ($(DEBUG), 1)
	CXX_DEFS += -DDEBUG
endif

SZ = size

CXXFLAGS=-Wall -std=c++17 $(CXX_DEFS) $(OPT) -c -fPIC -flto
CXXFLAGS += -MMD -MP -MF"$(@:%.o=%.d)"

LDFLAGS=-Wall -O3 -flto -shared -W

all: $(TARGET)


OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(CPP_SOURCES:.cc=.o)))
vpath %.cc $(sort $(dir $(CPP_SOURCES)))

$(BUILD_DIR)/%.o: %.cc Makefile | $(BUILD_DIR)
	$(CXX) -c $(CXXFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.cc=.lst)) $< -o $@

$(TARGET): $(OBJECTS) Makefile
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR):
	mkdir $@		


clean:
	rm -rf $(BUILD_DIR)