# TracOS ↔ Client Integration Flow

## Introduction

This repository contains a Python service that provides a robust, asynchronous integration between a client's system (simulated via JSON files) and an internal TracOS system (represented by a MongoDB database). The service handles the synchronization of work orders in both directions, ensuring data consistency between the two platforms.

The application is built with a modular and maintainable architecture, separating concerns into distinct layers for data access (repositories), data transformation (mappers), and orchestration (services).

## Architecture Overview

The integration flow is designed with a clear separation of concerns to enhance testability and future expansion:

* **`IntegrationService` (`src/main.py`):** The main orchestrator that controls the flow of data. It uses the repositories and mappers to process inbound and outbound work orders.
* **`TracOSRepository` (`src/tracos/repository.py`):** Handles all database operations for the TracOS system. It is responsible for creating, updating, and querying work orders in MongoDB, and includes resilient logic for database connection retries.
* **`ClientRepository` (`src/client/repository.py`):** Manages all file system interactions for the client's system. It reads inbound work order JSON files and writes outbound files.
* **`WorkorderMapper` (`src/translation/mapper.py`):** A pure logic module responsible for translating the data structure (payload) between the client's format and the TracOS format. It handles status mapping, date normalization, and field alignment.

## How the System Works

1.  **Inbound (Client → TracOS)**
    * Reads all `.json` files from the input folder specified by `DATA_INBOUND_DIR`.
    * For each valid work order, it uses `WorkorderMapper` to translate the client's data format into the TracOS format.
    * It then calls `TracOSRepository` to either insert a new work order or update an existing one (upsert logic) in the MongoDB collection.

2.  **Outbound (TracOS → Client)**
    * Queries MongoDB using `TracOSRepository` for all work orders marked with `isSynced: false`.
    * For each record, it translates the data from the TracOS format back to the client's format.
    * A new JSON file is written to the output folder (`DATA_OUTBOUND_DIR`).
    * Finally, the original record in MongoDB is marked with `isSynced: true` and a `syncedAt` timestamp to prevent reprocessing.

3.  **Execution Modes**
    * The application can be run in two modes, configured via the `RUN_MODE` environment variable:
        * **`once` (default):** Runs the inbound and outbound cycles once and then exits.
        * **`continuous`:** Runs the cycles continuously at a set interval, controlled by the `SYNC_INTERVAL_SECONDS` environment variable (default is 60 seconds).

## Setting Up The Project

### Prerequisites

* Python 3.11+
* Docker and Docker Compose
* Poetry
* make (optional)

### Installation Steps

1.  **Clone the repository**
    ```bash
    # Clone the repository using SSH
    git clone git@github.com:0bvim/integrations_engineering.git integrations-engineering

    # or using GitHub CLI
    gh repo clone 0bvim/integrations_engineering integrations-engineering

    # Navigate into the project directory
    cd integrations-engineering
    ```

2.  **Install dependencies with Poetry**
    ```bash
    # Install Poetry if you don't have it
    curl -sSL https://install.python-poetry.org | python3 -

    # Install project dependencies
    poetry install
    ```

3.  **Start MongoDB using Docker Compose**
    ```bash
    # If you have Docker and Docker Compose installed, you can start MongoDB with Docker Compose.
    docker-compose up -d

    # if you have docker compose v2+ installed, you can use:
    docker compose up -d

    # Or using make (optional, compose v2+)
    make mongo
    ```

4.  **Run the setup script to initialize sample data**
    ```bash
    # Run via command line
    poetry run python -m setup

    # or using make
    make setup
    ```

5.  **Configure environment variables**
    * Create a `.env` file in the root directory or export the variables directly in your shell.

    ```bash
    # .env file example
    echo 'MONGO_URI=mongodb://localhost:27017/tractian' > .env
    echo 'DATA_INBOUND_DIR=./data/inbound' >> .env
    echo 'DATA_OUTBOUND_DIR=./data/outbound' >> .env

    # For continuous execution
    echo 'RUN_MODE=continuous' >> .env
    echo 'SYNC_INTERVAL_SECONDS=60' >> .env
    ```

## Project Structure

```
integrations-engineering/
├── data/                             # Directory for input and output files
├── docker-compose.yml                # Docker Compose file to run MongoDB
├── poetry.lock                       # Poetry lock file for dependency versions
├── pyproject.toml                    # Poetry project configuration
├── README.md
├── conftest.py                       # Pytest configuration file
├── setup.py                          # Script to initialize sample data
├── src/                              # Source code directory
│   ├── client/                       # Client-side integration logic
│   ├── tracos/                       # TracOS-side integration logic
│   ├── translation/                  # Data transformation logic
│   ├── utils/                        # Utility functions and classes
│   ├── config.py                     # Configuration management
│   └── main.py                       # Main entry point for the integration service
└── tests/
    ├── e2e/
    │   └── test_flow.py              # End-to-end tests for the integration flow
    └── unity/
        ├── test_client.py            # Unit tests for client repository
        ├── test_mapper.py            # Unit tests for work order mapper
        ├── test_tracos_repository.py # Unit tests for TracOS repository
        └── test_utils.py             # Unit tests for utility functions
```

## Running the Application

1.  **To run the integration flow once:**
    ```bash
    # run in command line
    poetry run python src.main

    # or using make
    make
    ```

2.  **To run the integration flow continuously:**
    ```bash
    # run in command line
    RUN_MODE=continuous poetry run python src.main

    # or using make
    make run

    # To run with a different sync interval
    make run SYNC_INTERVAL_SECONDS=30

    # default interval running with `make run` is 5 seconds
    ```

## Testing

The project has a comprehensive test suite covering different layers of the application.

* **Unit Tests:** These tests cover individual modules in isolation, using mocks to simulate external dependencies like the database or file system. They test the `WorkorderMapper`, `TracOSRepository`, `ClientRepository`, and utility modules.
* **End-to-End (E2E) Tests:** A full E2E test verifies the complete integration flow from reading an inbound file to writing an outbound file, using a mocked database to ensure speed and reliability without requiring a running Docker container for tests.

Run all tests with:
```bash
# Run all tests in the project in command line
poetry run pytest

# or using make
make tests # run all tests

# To run only unit tests
make tests_unity

# To run only end-to-end tests
make test_e2e

# To run tests with verbose output (all listed above)
make tests VERBOSE=-v
```

## Troubleshooting

* **MongoDB Connection Issues**: If using the real database, ensure Docker is running and the MongoDB container is up with `docker ps`.
* **Missing Dependencies**: Verify your Poetry environment is activated or run `poetry install` again.
* **Permission Issues**: Check file permissions for the `data/` and `logs/` directories.
