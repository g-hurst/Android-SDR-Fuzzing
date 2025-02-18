SUBDIR = $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# link to docs https://github.com/srsran/srsRAN_Project/tree/main/docker
# this is the ssh url of the forked repo - make sure to have key setup
SRSRAN_REPO_URL    = https://github.com/g-hurst/srsRAN_Project.git
SRSRAN_REPO_DIR    = $(SUBDIR)/../srsRAN_Project
SRSRAN_DOCKER_PATH = $(SUBDIR)/docker-compose.yml
# cone repo if needed
.PHONY: srsran-check-clone
srsran-check-clone:
ifeq ($(wildcard $(SRSRAN_REPO_DIR)),)
# the repository directory does not exist
	@echo "Cloning repository $(SRSRAN_REPO_URL)..."
	git clone $(SRSRAN_REPO_URL) $(SRSRAN_REPO_DIR) || echo "failed to clone srsRAN_Project"
else ifeq ($(wildcard $(SRSRAN_REPO_DIR)/*),)
# the repository directory is empty
	@echo "Cloning repository $(SRSRAN_REPO_URL)..."
	git clone $(SRSRAN_REPO_URL) $(SRSRAN_REPO_DIR) || echo "failed to clone srsRAN_Project"
else
	@echo "Repository $(REPO_DIR) already exists."
endif


.PHONY: srsran-run
srsran-run: 
	cp -f $(SUBDIR)/../configs/* $(SRSRAN_REPO_DIR)/configs/
	docker compose -f $(SRSRAN_DOCKER_PATH) up

.PHONY: srsran-build
srsran-build: srsran-check-clone
	cp -f $(SUBDIR)/../configs/* $(SRSRAN_REPO_DIR)/configs/
	docker compose -f $(SRSRAN_DOCKER_PATH) build

.PHONY: srsran-reclone
srsran-reclone:
# delete the directory if it exists
ifneq ($(wildcard $(SRSRAN_REPO_DIR)),)
	rm -rf $(SRSRAN_REPO_DIR)
endif
# clone the repo
	$(MAKE) srsran-check-clone

# removes pruned docker images that are >24h old
.PHONY: docker-clean-images
docker-clean-images:
	docker image prune -a --filter "until=24h"

.PHONY: docker-network-clear
docker-network-clear:
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "Error: $(MAKECMDGOALS) must be run as sudo"; \
		exit 1; \
	fi
	sudo systemctl stop docker
	sudo rm -rf /var/lib/docker/network/
	sudo systemctl start docker

