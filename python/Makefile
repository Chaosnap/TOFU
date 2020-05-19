PICKLE_CLEANLIST:=$(wildcard ./traces/*.pickle)
DATABASE_CLEANLIST:=$(wildcard ./traces/*.db)
JSON_CLEANLIST:=$(wildcard ./traces/*.json)

all:
	@echo "ich bin eine katze und weiß von nichts"

env:
	bash setup_tofu_python.sh

envclean:
	rm -rf tofu_python

clean:
	rm -f $(PICKLE_CLEANLIST) $(DATABASE_CLEANLIST) $(JSON_CLEANLIST)


