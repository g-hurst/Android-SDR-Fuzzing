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

.PHONY: build-docs
build-docs:
	sphinx-apidoc -o ./docs ./app
	cd ./docs && make html

.PHONY: run-docs
run-docs:
	cd ./docs/_build/html/ && python3 -m http.server 8088
