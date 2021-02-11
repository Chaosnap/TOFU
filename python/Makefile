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


venvclean:
	rm -rf tofu_python