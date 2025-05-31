import os
from loguru import logger

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/tractian")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "tractian")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")

# File system directories
DATA_INBOUND_DIR = os.getenv("DATA_INBOUND_DIR", "./data/inbound")
DATA_OUTBOUND_DIR = os.getenv("DATA_OUTBOUND_DIR", "./data/outbound")

# Ensure directories exist
for directory in [DATA_INBOUND_DIR, DATA_OUTBOUND_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
