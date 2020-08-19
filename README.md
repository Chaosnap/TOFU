	 _____ ___  _____ _   _ 
	|_   _/ _ \|  ___| | | |
	  | || | | | |_  | | | |
	  | || |_| |  _| | |_| |
	  |_| \___/|_|    \___/ 

### Toggle Analysis in more than 20 lines of code.

TOFU is a versatile tool to translate Value Change Dumps (VCDs) into power traces which can be used for Test Vector Leakage Assessment (TVLA).

# List of files
	python/parse.py # vcd parser
	python/synthesize.py #generate synthetic power traces
	python/analyze.py #welch t test
	python/settings.json #settings

# HOWTO

  1. Gather VCD traces
  2. Adjust settings file `settings.json` accordingly
  3. run `python3 parse.py --settings example/settings_example.json`
  4. run `python3 synthesize.py --settings example/settings_example.json`
  5. run `python3 analyze.py --settings example/settings_example.json`
 
 # Contact
 [Michael Gruber](https://www.ei.tum.de/sec/mitarbeiter/michael-gruber/), [m.gruber@tum.de](mailto:m.gruber@tum.de)