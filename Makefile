VENV=source tofu_python/bin/activate
NRPOC:=$(shell nproc)
SHELL:=$(shell which bash)

all:
	@echo "ich bin eine katze und weiß von nichts"

clean:
	make -C example clean
	make -C example-aes-vhdl clean
	make -C engine clean

venv:
	@[ -d tofu_python ] || bash setup_tofu_python.sh

engine:
	make -C engine

venv_attack_framework: venv
	bash setup_attack_framework.sh

example: clean venv
	$(VENV); python3 parse.py --settings example/settings_example.json
	$(VENV); python3 extractsignalids.py --settings example/settings_example.json
	$(VENV); python3 synthesize.py --settings example/settings_example.json
	@#$(VENV); python3 analyze.py --settings example/settings_example.json

example_aes: clean venv
	$(VENV); make -C example-aes-vhdl clean cleansim get_sources
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	$(VENV); make -C example-aes-vhdl dpa

example_aes_filtered: clean venv
	$(VENV); make -C example-aes-vhdl clean cleansim get_sources
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	@# generate filtered signals.json
	$(VENV); python3 extractsignalids.py --settings example-aes-vhdl/settings_example.json
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	$(VENV); make -C example-aes-vhdl dpa

ntofu_example_aes: clean venv engine
	$(VENV); make -C example-aes-vhdl clean cleansim get_sources
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); make -C example-aes-vhdl ntofu
	$(VENV); make -C example-aes-vhdl dpa

selftest: venv engine
	$(VENV); bash selftest.sh

pep: venv
	$(VENV); black ./

pep_check: venv
	$(VENV); black --check  --diff .

venvclean:
	rm -rf tofu_python

.PHONY: engine