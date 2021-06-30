VENV=source tofu_python/bin/activate
NRPOC:=$(shell nproc)

all:
	@echo "ich bin eine katze und weiß von nichts"

clean:
	rm -f example/*.pickle
	rm -f example/*.h5
	rm -f example/signals.json
	make -C example-aes-vhdl clean

venv:
	bash setup_tofu_python.sh

venv_attack_framework: venv
	bash setup_attack_framework.sh

example: clean
	$(VENV); python3 parse.py --settings example/settings_example.json
	$(VENV); python3 extractsignalids.py --settings example/settings_example.json
	$(VENV); python3 synthesize.py --settings example/settings_example.json
	@#$(VENV); python3 analyze.py --settings example/settings_example.json

example_aes: clean
	$(VENV); make -C example-aes-vhdl clean cleansim get_sources
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	$(VENV); make -C example-aes-vhdl dpa

example_aes_filtered: clean
	$(VENV); make -C example-aes-vhdl clean cleansim get_sources
	$(VENV); make -C example-aes-vhdl simulate -j $(NRPOC)
	$(VENV); python3 parse.py --settings example-aes-vhdl/settings_example.json
	@# generate filtered signals.json
	$(VENV); python3 extractsignalids.py --settings example-aes-vhdl/settings_example.json
	$(VENV); python3 synthesize.py --settings example-aes-vhdl/settings_example.json --loglevel warning
	$(VENV); make -C example-aes-vhdl dpa

pep:
	$(VENV); black ./

pep_check:
	$(VENV); black --check  --diff .

venvclean:
	rm -rf tofu_python