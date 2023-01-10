	 _____ ___  _____ _   _ 
	|_   _/ _ \|  ___| | | |
	  | || | | | |_  | | | |
	  | || |_| |  _| | |_| |
	  |_| \___/|_|    \___/ 

### Toggle Analysis in more than 20 lines of code.

TOFU is a versatile tool to translate Value Change Dumps (VCDs) into power traces which can be used for further analysis like DPA/TVLA.
The according eprint is available at the [Cryptology ePrint Archive](https://eprint.iacr.org/2022/129).

# List of files

	.
	├── example                      # folder with the basic example (use this folder as a template)
	├── example-aes-vhdl             # folder with the vhdl aes example requires ghdl
	├── example-aes-cortex           # folder with the cortex aes example requires unicorn
	├── example-kat                  # folder with the kat example
	├── extractsignalids.py          # extract signal ids based on signal names
	├── HOWTO.md                     # how to get started with tofu
	├── Makefile                     # Makefile to build venv and run example
	├── parse.py                     # parse vcd files
	├── plotme.py                    # sample plotting file for a ttes
	├── README.md                    # the file you are looking at
	├── selftest.sh                  # selftest wrapper script
	├── selftest.py                  # selftest compare ntofu with tofu (AES example)
	├── setup_attack_framework.sh    # setup the attack framework TUEISEC intern only
	├── setup_tofu_python.sh         # setup tofu venv
	├── signals.py                   # dump signals to dictionary (debugging)
	├── synthesize.py                # synthesize power traces
	├── tueisec.py                   # tueisec export helper
	└── value.py                     # extract values from vcd trace

# HOWTO

[Further explanation on the usage](./HOWTO.md).

# Contact

[Michael Gruber](https://www.ce.cit.tum.de/eisec/mitarbeiter/michael-gruber/), [m.gruber@tum.de](mailto:m.gruber@tum.de)

# Pipeline

[![pipeline status](https://gitlab.lrz.de/TUEISEC-Intern/tofu/badges/master/pipeline.svg)](https://gitlab.lrz.de/TUEISEC-Intern/tofu/commits/master)
