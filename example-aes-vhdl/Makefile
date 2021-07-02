NR_SIMULATIONS?=100
NUMBERS:=$(shell seq 1 ${NR_SIMULATIONS})

SIMS:=$(addprefix vcd/aes, ${NUMBERS})
SIMS:=$(addsuffix .vcd, ${SIMS})

TVS:=$(addprefix testvector/testvector, ${NUMBERS})
TVS:=$(addsuffix .tv, ${TVS})

all:
	@echo "make aes_vhdl"
	@echo "make simulate -j numberofcores"
	@echo "make attack"

aes_vhdl: get_sources test_enc

simulate: test_enc $(TVS) $(SIMS)

attack: dpa

get_sources:
	[ -d aes-vhdl ] || git clone https://github.com/hadipourh/AES-VHDL aes-vhdl

dpa:
	python3 dpa_lascar.py
	cat generate_testvectors.py | grep key | head -n 1

ntofu:
	python3 ../ntofu.py --settings ntofu_settings_example.json

clean:
	rm -rf aes-vhdl-work
	rm -f correlation.pdf
	rm -f correlation.h5
	rm -f traces.h5
	rm -f test_enc
	rm -f *test_enc.o
	rm -f signals.json
	rm -f tofu_traces.h5
	rm -f ntofu_traces.h5
	rm -f signal_properties_meta.pickle
	rm -f signal_properties.pickle

cleansim:
	rm -rf testvector/
	rm -rf vcd/

test_enc:
	mkdir -p aes-vhdl-work
	ghdl -i --workdir=aes-vhdl-work aes-vhdl/AES-ENC/RTL/*.vhd enc_tb.vhd
	ghdl -m --workdir=aes-vhdl-work test_enc

testvector/testvector%.tv:
	@mkdir -p testvector
	@echo "generating testvector $*"
	@python3 generate_testvectors.py testvector/testvector$*.tv $*

vcd/aes%.vcd: testvector/testvector%.tv test_enc
	@mkdir -p vcd
	@echo "running simulation $*"

	@# The testbench requires key and plaintext as arguments.
	@# Both are split into 8 shares.
	@filename="testvector/testvector$*.tv" ; \
	f=$$(cat $$filename) ; \
	args="" ; \
	for i in $$(seq 0 7) ; do \
		pi=$$(echo $$f | cut -c$$((1+i*4))-$$(((i+1)*4))) ; \
		args="$$args -gp$$i=16#$$pi#" ; \
		ki=$$(echo $$f | cut -c$$((34+i*4))-$$((33+(i+1)*4))) ; \
		args="$$args -gk$$i=16#$$ki#" ; \
	done ; \
	ghdl -r --workdir=aes-vhdl-work test_enc --vcd=vcd/aes$*.vcd $$args --stop-time=25ms