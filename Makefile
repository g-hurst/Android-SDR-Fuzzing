include app/controller/docker/Makefile

.DEFAULT_GOAL := srsran-build

.PHONY: setup
setup:
	pip install -r ./app/requirements.txt

.PHONY: test
test:
	pytest --ignore=$(SRSRAN_REPO_DIR)

.PHONY: clean
clean:
	$(MAKE) docker-clean-images
	rm -rf ./app/controller/.android/
	rm -rf ./.pytest_cache/
