include app/controller/docker/Makefile
include app/Makefile

.DEFAULT_GOAL := srsran-build

.PHONY: test
test:
	pytest --ignore=$(SRSRAN_REPO_DIR)

.PHONY: clean
clean:
	$(MAKE) docker-clean-images
	rm -rf ./app/controller/.android/
	rm -rf ./.pytest_cache/
