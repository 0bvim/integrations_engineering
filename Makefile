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

.PHONY: mongo
test:
	@echo "Running tests (not implemented yet)"
