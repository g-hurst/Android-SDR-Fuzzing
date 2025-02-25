SUBDIR = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: setup
setup:
	pip install -r ./app/requirements.txt

# this is currently hard coded to garrett's eth adapter name,
# make sure to change it when running on another device
NET_DEV := enx00e04c681f5a
.PHONY: run-app
run-app: setup
	$(SUBDIR)/main.py


