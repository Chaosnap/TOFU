PICKLE_CLEANLIST:=$(wildcard ./traces_behav/*.pickle) $(wildcard ./traces_func/*.pickle)
DATABASE_CLEANLIST:=$(wildcard ./traces_behav/*.db) $(wildcard ./traces_func/*.db)
JSON_CLEANLIST:=$(wildcard ./traces_behav/*.json) $(wildcard ./traces_func/*.json)

all:
	@echo "ich bin eine katze und weiß von nichts"

env:
	bash setup_tofu_python.sh

envclean:
	rm -rf tofu_python

clean:
	rm -f $(PICKLE_CLEANLIST) $(DATABASE_CLEANLIST) $(JSON_CLEANLIST)


