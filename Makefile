VENV?=source tofu_python/bin/activate
NRPOC:=$(shell nproc)
SHELL:=$(shell which bash)
LOGLEVEL?=info


all:
	@echo "ich bin eine katze und weiß von nichts"

venv:
	@[ -d tofu_python ] || bash setup_tofu_python.sh

venv_lascar: venv
	bash setup_lascar.sh

venv_attack_framework: venv
	bash setup_attack_framework.sh

engine:
	make -C engine

example: clean venv
	$(VENV); python3 parse.py --settings example/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 extractsignalids.py --settings example/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 synthesize.py --settings example/settings_example.json --loglevel $(LOGLEVEL)

example_aes: clean venv
	$(VENV); make -C example-aes-vhdl clean cleansim
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); make -C example-aes-vhdl dpa

example_aes_filtered: clean venv
	$(VENV); make -C example-aes-vhdl clean cleansim
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json --loglevel $(LOGLEVEL)
	@# generate filtered signals.json
	$(VENV); python3 extractsignalids.py --settings example-aes-vhdl/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel $(LOGLEVEL)
	$(VENV); make -C example-aes-vhdl dpa 

ntofu_example_aes: clean venv engine
	$(VENV); make -C example-aes-vhdl clean cleansim
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); make -C example-aes-vhdl ntofu
	$(VENV); make -C example-aes-vhdl dpa DPA_SETTINGS_FILE=ntofu_settings_example.json

selftest: venv engine
	$(VENV); bash selftest.sh

pep: venv
	$(VENV); black ./

pep_check: venv
	$(VENV); black --check  --diff .

clean:
	make -C example clean
	make -C example-aes-vhdl clean
	make -C engine clean
	rm -rf __pycache__

venvclean:
	rm -rf tofu_python

.PHONY: engine