# makefile commands


srsran-check-clone
* checks if the srsRAN repo exists and is non-empty
* clones the repo if either above condition is true
* **The clone link is ssh, so an ssh key must be loaded in github**

srsran-reclone
* deletes the folder for srsRAN if it exists
* runs srsran-check-clone

srsran-run
* runs srsran-check-clone
* runs docker compose up with the dockerfile in **OUR REPO's**
config files (`app/controller/docker`, and `app/controller/configs/`)

docker-clean-images
* deletes all docker images that are >24 hr old AND not associated with a container
