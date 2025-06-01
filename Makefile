RUN_MODE := continuous
SYNC_INTERVAL_SECONDS := 3

.PHONY: all
all:
	@poetry run python3 -m src.main

.PHONY: run
run:
	# to change environment variables
	# run `make run RUN_MODE=continuous SYNC_INTERVAL_SECONDS=3`
	@RUN_MODE=$(RUN_MODE) \
	SYNC_INTERVAL_SECONDS=$(SYNC_INTERVAL_SECONDS) \
	poetry run python3 -m src.main

# deprecated target, use 'test' instead
.PHONY: test_config_py
test_config_py:
	@echo "Running tests for config.py"
	@python3 src/config.py

# deprecated target, use 'test' instead
.PHONY: test_logger_py
test_logger_py:
	@echo "Running tests for logger.py"
	@python3 src/logger_config.py

.PHONY: mongo
mongo:
	@echo "starting MongoDB"
	@docker compose up -d

.PHONY: setup
setup:
	@echo "Setting up the environment"
	@poetry run python -m setup

.PHONY: clean_data
clean_data:
	@echo "Cleaning data inbound and outbound directories"
	@rm -rf data/inbound/*
	@rm -rf data/outbound/*

.PHONY: tests
tests:
	@echo "Running tests"
	# Use VERBOSE=-v to enable verbose output
	@poetry run pytest $(VERBOSE) --maxfail=1 --disable-warnings

.PHONY: tests_unity
tests_unity:
	@echo "Running Unity tests"
	# Use VERBOSE=-v to enable verbose output
	@poetry run pytest $(VERBOSE) --maxfail=1 --disable-warnings tests/unity/*

.PHONY: test_e2e
test_e2e:
	@echo "Running E2E tests"
	# Use VERBOSE=-v to enable verbose output
	@poetry run pytest $(VERBOSE) --maxfail=1 --disable-warnings tests/e2e/test_flow.py
