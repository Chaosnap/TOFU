
TRACES_SOURCES:=$(wildcard ./traces/*.vcd)
TRACES_BASENAME:=$(basename $(TRACES_SOURCES))

CLEAN_SUFFIXES_TRACES:= .pickle

TRACES_CLEANLIST:= $(foreach suffix,$(CLEAN_SUFFIXES_TRACES),$(addsuffix $(suffix),$(TRACES_BASENAME)))

GIT_REV_LIST:=$(shell git rev-list --count HEAD)
GIT_REV_PARSE:=$(shell git rev-parse HEAD)
GIT_STATUS_SHORT:=$(shell git status --short | tr "\n" " ")
TIMESTAMP:=$(shell date)

all:
	@echo "ich bin eine katze und weiß von nichts"

env:
	bash setup_tofu_python.sh

envclean:
	rm -rf tofu_python

clean:
	rm -f $(TRACES_CLEANLIST)


