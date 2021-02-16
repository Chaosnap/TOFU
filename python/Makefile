VENV=source tofu_python/bin/activate

all:
	@echo "ich bin eine katze und weiß von nichts"

clean:
	rm -f example/*.pickle
	rm -f example/*.h5
	rm -f example/signals.json

venv:
	bash setup_tofu_python.sh

venv_attack_framework: venv
	bash setup_attack_framework.sh

example: clean
	$(VENV); python3 parse.py --settings example/settings_example.json
	$(VENV); python3 synthesize.py --settings example/settings_example.json
	$(VENV); python3 analyze.py --settings example/settings_example.json

venvclean:
	rm -rf tofu_python