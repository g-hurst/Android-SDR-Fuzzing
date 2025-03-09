.DEFAULT_GOAL := setup

.PHONY: setup
setup:
	pip install -r ./app/requirements.txt

.PHONY: run
run:
	cd ./app && /main.py -i

.PHONY: test
test:
	pytest

.PHONY: clean
clean:
	rm -rf ./app/controller/.android/
	rm -rf ./.pytest_cache/
