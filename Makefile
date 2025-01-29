# link to docs https://github.com/srsran/srsRAN_Project/tree/main/docker
# this is the ssh url of the forked repo - make sure to have key setup
SRSRAN_REPO_URL    = git@github.com:g-hurst/srsRAN_Project.git 
SRSRAN_REPO_DIR    = app/controller/srsRAN_Project
SRSRAN_DOCKER_PATH = $(SRSRAN_REPO_DIR)/docker/docker-compose.yml
# cone repo if needed
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


.phony: srsran-reclone
srsran-reclone:
# delete the directory if it exists
ifneq ($(wildcard $(SRSRAN_REPO_DIR)),)
	rm -rf $(SRSRAN_REPO_DIR)
endif
# clone the repo
	$(MAKE) srsran-check-clone

# removes pruned docker images that are >24h old
.phony: docker-clean-images
docker-clean-images:
	docker image prune -a --filter "until=24h"
