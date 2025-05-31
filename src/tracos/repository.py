from datetime import datetime, timezone
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from bson import ObjectId
import asyncio

from src.config import MONGO_URI, MONGO_DATABASE, MONGO_COLLECTION

class TracOSRepository:
    """Repository for interacting with TracOS MongoDB database"""

    def __init__(self, mongo_uri: str = MONGO_URI, db_name: str = MONGO_DATABASE, collection_name: str = MONGO_COLLECTION):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.retry_attempts = 3
        self.retry_delay = 2

    async def connect(self):
        """Establish connection to MongoDB"""
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Connecting to MongoDB (attempt {attempt + 1}/{self.retry_attempts})...")
                self.client = AsyncIOMotorClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
                await self.client.admin.command('ping')

                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                logger.info("Successfully connected to MongoDB")
                return
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB on attempt {attempt + 1}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Max retry attempts reached, could not connect to MongoDB")
                    raise ConnectionError("Could not connect to MongoDB after several attempts")

    async def disconnect(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def get_unsynchronized_workorders(self) -> List[Dict[str, Any]]:
        """Get all workorders that have not been synchronized yet"""
        try:
            cursor = self.collection.find({"isSynced": False})
            return await cursor.to_list(length=100)
        except Exception as e:
            logger.error(f"Error retrieving unsynchronized workorders: {e}")
            return []

    async def create_or_update_workorder(self, workorder: Dict[str, Any]) -> bool:
        """Create a new workorder or update an existing one, with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                existing = await self.collection.find_one({"number": workorder["number"]})

                if existing:
                    if self.compare_items(existing, workorder):
                        logger.info(f"Workorder {workorder['number']} is already up-to-date, skipping")
                        return True

                    update_data = {**workorder, "updatedAt": datetime.now(timezone.utc), "isSynced": False}
                    result = await self.collection.update_one(
                        {"number": workorder["number"]},
                        {"$set": update_data}
                    )
                    logger.info(f"Updated workorder {workorder['number']}")
                    return result.modified_count > 0
                else:
                    workorder["createdAt"] = datetime.now(timezone.utc)
                    workorder["updatedAt"] = workorder["createdAt"]
                    workorder["isSynced"] = False
                    result = await self.collection.insert_one(workorder)
                    logger.info(f"Created workorder {workorder['number']}")
                    return bool(result.inserted_id)

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.retry_attempts} failed for workorder {workorder.get('number')}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Max retries reached for workorder {workorder.get('number')}. Giving up.")
                    return False
        return False

    async def mark_as_synced(self, workorder_id: str) -> bool:
        """Mark a workorder as synchronized"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(workorder_id)},
                {
                    "$set": {
                        "isSynced": True,
                        "syncedAt": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking workorder {workorder_id} as synced: {e}")
            return False

    def compare_items(self, inbound, outbound) -> bool:
        """Compare two workorder items for equality"""
        keys = ["description", "status", "title", "deleted"]
        filtered_inbound = {k: v for k, v in inbound.items() if k in keys}
        filtered_outbound = {k: v for k, v in outbound.items() if k in keys}
        return filtered_inbound == filtered_outbound
