NAME   := virtualipmi
TAG    := 1.0
IMAGE  := ${NAME}:${TAG}
LATEST := ${NAME}:latest

IPMI_LISTEN_PORT?=623
IPMI_USER?=admin
IPMI_PASSWORD?=admin
IPMI_MANAGED_HOST?=localhost
IPMI_LOG_FILE?=/root/logs/$(IPMI_MANAGED_HOST).log

define optbool
$(filter $(shell echo $(1) | tr A-Z a-z),yes on 1)
endef

all:
	@echo "make build      # Build the Docker image '$(IMAGE)'"
	@echo "make run        # Run example (it will rebuild the image)"
	@echo "make tox        # Run code linters (it will rebuild the image)"
	@echo "make clean      # Remove garbage"
	@echo "make clean-all  # Remove all garbage include the linter's data"

build:
	docker build --rm $(if $(call optbool,$(NC)),--no-cache,) -t $(IMAGE) .
	docker tag ${IMAGE} ${LATEST}

run: build
	docker run --rm \
			--volume `pwd`/scripts:/root/scripts:ro \
			--volume `pwd`/logs:/root/logs:rw \
			--publish 623:$(IPMI_LISTEN_PORT)/udp \
			--env IPMI_USER=$(IPMI_USER) \
			--env IPMI_PASSWORD=$(IPMI_PASSWORD) \
			--env IPMI_MANAGED_HOST=$(IPMI_MANAGED_HOST) \
			--env IPMI_LOG_FILE=$(IPMI_LOG_FILE) \
		-it $(IMAGE)

tox: build
	time docker run --rm \
			--volume `pwd`:/root/src:ro \
			--volume `pwd`/linters:/root/src/linters:rw \
		-it $(IMAGE) tox -q -c /root/src/linters/tox.ini $(if $(E),-e $(E),-p auto)

clean:
	-find __pycache__ | xargs rm -rf

clean-all: clean
	rm -f logs/*.log
	docker run --rm \
			--volume `pwd`:/root/src:rw \
		-it $(IMAGE) bash -c "rm -rf /root/src/linters/{.tox,.mypy_cache}"
