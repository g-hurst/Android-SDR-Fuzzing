include app/controller/docker/Makefile

.DEFAULT_GOAL := srsran-build

.PHONY: test
test:
	@echo 'there curretnly are no tests, but we will write them...'

.PHONY: clean
clean:
	$(MAKE) docker-clean-images
