	 _____ ___  _____ _   _ 
	|_   _/ _ \|  ___| | | |
	  | || | | | |_  | | | |
	  | || |_| |  _| | |_| |
	  |_| \___/|_|    \___/ 

### Toggle Analysis in more than 20 lines of code.

TOFU is a versatile tool to translate Value Change Dumps (VCDs) into power traces which can be used for further analysis like DPA/TVLA.

# List of files

	.
	├── example                      # folder with the basic example
	├── example-aes-vhdl             # folder with the aes example requires ghdl
	├── extractsignalids.py          # extract signal ids based on signal names
	├── Makefile                     # Makefile to build venv and run example
	├── parse.py                     # parse vcd files
	├── plotme.py                    # sample plotting file for a ttes
	├── README.md                    # the file you are looking at
	├── setup_attack_framework.sh    # setup the attack framework TUEISEC intern only
	├── setup_tofu_python.sh         # setup tofu venv
	├── signals.py                   # dump signals to dictionary (debugging)
	├── synthesize.py                # synthesize power traces
	├── tueisec.py                   # tueisec export helper
	└── value.py                     # extract values from vcd trace

# HOWTO

  1. Gather VCD traces
  2. Adjust settings file `settings.json` accordingly
  3. `python3 parse.py --settings example/settings_example.json`
  4. `python3 extractsignalids.py --settings example/settings_example.json`
  5. `python3 synthesize.py --settings example/settings_example.json`
 
 # Contact
 [Michael Gruber](https://www.ei.tum.de/sec/mitarbeiter/michael-gruber/), [m.gruber@tum.de](mailto:m.gruber@tum.de)

# Pipeline

[![pipeline status](https://gitlab.lrz.de/TUEISEC-Intern/tofu/badges/master/pipeline.svg)](https://gitlab.lrz.de/TUEISEC-Intern/tofu/commits/master)
