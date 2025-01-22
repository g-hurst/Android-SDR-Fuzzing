
# some convienient commands for the open5gs repo
# The docs are linked here: https://github.com/open5gs/open5gs/tree/main/docker
OPEN5GS_REPO_URL    = https://github.com/open5gs/open5gs.git
OPEN5GS_REPO_DIR    = app/open5gs
OPEN5GS_DOCKER_PATH = $(OPEN5GS_REPO_DIR)/docker/docker-compose.yml
# checks that the repository directory exists and clones open5gs if it does not
.phony: open5gs-check-clone
open5gs-check-clone:
ifeq ($(wildcard $(OPEN5GS_REPO_DIR)),)
	@echo "Cloning repository $(OPEN5GS_REPO_URL)..."
	git clone $(OPEN5GS_REPO_URL) $(OPEN5GS_REPO_DIR)
else
	@echo "Repository $(REPO_DIR) already exists."
endif
# run the docker compose test command
.phony: open5gs-test
open5gs-test: open5gs-check-clone
	docker compose -f $(OPEN5GS_DOCKER_PATH) run test
