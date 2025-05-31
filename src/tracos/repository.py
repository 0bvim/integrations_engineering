from datetime import datetime, timezone
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from bson import ObjectId
import asyncio

from src.config import MONGO_URI, MONGO_DATABASE, MONGO_COLLECTION

class TracOSRepository:
    """Repository for interacting with TracOS MongoDB database"""

    db, collection, client = [None, None, None]
    def __init__(self, mongo_uri: str = MONGO_URI):
        self.mongo_uri = mongo_uri
        self.retry = 1

    async def connect(self):
        """Establish connection to MongoDB"""
        self.client = None
        if not self.client:
            logger.info("Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(self.mongo_uri, connectTimeoutMS=500, timeoutMS=500)

            pong = await self.client.admin.command('ping')
            if pong != {'ok': 1.0}:
                logger.error("Failed to connect to MongoDB")
                raise ConnectionError("Could not connect to MongoDB")

            self.db = self.client[MONGO_DATABASE]
            self.collection = self.db[MONGO_COLLECTION]
            logger.info("Connected to MongoDB")

    async def get_unsynchronized_workorders(self) -> List[Dict[str, Any]]:
        """Get all workorders that have not been synchronized yet"""
        try:
            cursor = self.collection.find({"isSynced": False})
            return await cursor.to_list(length=100)
        except Exception:
            logger.error("Error retrieving unsynchronized workorders: failed to connect to MongoDB")
            return []

    async def create_or_update_workorder(self, workorder: Dict[str, Any]) -> bool:
        """Create a new workorder or update an existing one"""
        try:
            existing = await self.collection.find_one({"number": workorder["number"]})

            if existing:
                if self.compare_items(existing, workorder):
                    logger.info(f"Workorder {workorder['number']} is already up-to-date, skipping")
                    return True
                result = await self.collection.update_one(
                    {"number": workorder["number"]},
                    {"$set": {**workorder, "updatedAt": datetime.now(timezone.utc), "isSynced": False}}
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
        except Exception:
            logger.error(f"Error creating/updating workorder: mongoDB connection failed: retrying... {self.retry}")
            self.retry += 1

            if self.retry > 3:
                logger.error("Max retries reached, giving up on creating/updating workorder")
                exit(1)

            await asyncio.sleep(1) # Retry after a short delay
            try:
                return await self.create_or_update_workorder(workorder)
            except Exception:
                logger.error("Retry failed: could not create/update workorder")
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
