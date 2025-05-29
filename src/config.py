import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DATABASE_NAME = MONGO_URI.split('/')[-1].split('?')[0] if MONGO_URI else "tractian" # Extracts db name
WORK_ORDERS_COLLECTION = "work_orders"

# Data Directories Configuration
DATA_INBOUND_DIR = os.getenv("DATA_INBOUND_DIR")
DATA_OUTBOUND_DIR = os.getenv("DATA_OUTBOUND_DIR")

# Logging Configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Translation Mappings
# Client Status -> TracOS Status
CLIENT_TO_TRACOS_STATUS_MAP = {
    "NEW": "created",
    "IN_PROGRESS": "in_progress", # Assuming client might use this
    "PENDING": "in_progress",   # Or this
    "OPEN": "created",
    "DONE": "completed",
    "CLOSED": "completed",
}

# TracOS Status -> Client Status
# Reverse mapping.
TRACOS_TO_CLIENT_STATUS_MAP = {
    "created": "NEW",
    "in_progress": "IN_PROGRESS",
    "completed": "DONE",
}

# Required fields for inbound client data validation
CLIENT_REQUIRED_FIELDS = ["id", "status", "createdAt", "title"]

def validate_config():
    """Validates that essential configurations are set."""
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable not set.")
    if not DATA_INBOUND_DIR:
        raise ValueError("DATA_INBOUND_DIR environment variable not set.")
    if not DATA_OUTBOUND_DIR:
        raise ValueError("DATA_OUTBOUND_DIR environment variable not set.")

    # Create data directories if they don't exist
    for dir_path in [DATA_INBOUND_DIR, DATA_OUTBOUND_DIR]:
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        else:
            logging.error(f"Directory path is None, cannot create. This indicates a missing env var.")


if __name__ == "__main__":
    # Basic test to print loaded config
    print(f"MONGO_URI: {MONGO_URI}")
    print(f"MONGO_DATABASE_NAME: {MONGO_DATABASE_NAME}")
    print(f"DATA_INBOUND_DIR: {DATA_INBOUND_DIR}")
    print(f"DATA_OUTBOUND_DIR: {DATA_OUTBOUND_DIR}")
    try:
        validate_config()
        print("Configuration validated successfully.")
    except ValueError as e:
        print(f"Configuration Error: {e}")
