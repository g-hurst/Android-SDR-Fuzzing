# link to docs https://github.com/srsran/srsRAN_Project/tree/main/docker
SRSRAN_REPO_URL    = https://github.com/srsran/srsRAN_Project.git
SRSRAN_REPO_DIR    = app/srsRAN_Project
SRSRAN_DOCKER_PATH = $(SRSRAN_REPO_DIR)/docker/docker-compose.yml
# checks that the repository directory exists and clones open5gs if it does not
.phony: srsran-check-clone
srsran-check-clone:
ifeq ($(wildcard $(SRSRAN_REPO_DIR)),)
# the repository directory does not exist
	@echo "Cloning repository $(SRSRAN_REPO_URL)..."
	git clone $(SRSRAN_REPO_URL) $(SRSRAN_REPO_DIR)
else ifeq ($(wildcard $(SRSRAN_REPO_DIR)/*),)
# the repository directory is empty
		@echo "Cloning repository $(SRSRAN_REPO_URL)..."
		git clone $(SRSRAN_REPO_URL) $(SRSRAN_REPO_DIR)
else
	@echo "Repository $(REPO_DIR) already exists."
endif
.phony: srsran-run
srsran-run: srsran-check-clone
	docker compose -f $(SRSRAN_DOCKER_PATH) up


# removes pruned docker images that are >24h old
.phony: docker-clean-images
docker-clean-images:
	docker image prune -a --filter "until=24h"
