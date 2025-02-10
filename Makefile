include app/controller/docker/Makefile

.DEFAULT_GOAL := srsran-build

.PHONY: test
test:
	pytest --ignore=$(SRSRAN_REPO_DIR)

.PHONY: clean
clean:
	$(MAKE) docker-clean-images
