import pytest
import os
import json
import shutil
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import pytest_asyncio

from src.main import IntegrationService
from src.tracos.repository import TracOSRepository
from src.client.repository import ClientRepository

# Test configuration for MongoDB
TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_MONGO_DB = "tractian_test_e2e"
TEST_MONGO_COLLECTION = "workorders_e2e"

@pytest.fixture
def test_dirs():
    """Creates temporary test directories for input and output data."""
    base_dir = "./test_data_e2e"
    inbound_dir = os.path.join(base_dir, "inbound")
    outbound_dir = os.path.join(base_dir, "outbound")
    os.makedirs(inbound_dir, exist_ok=True)
    os.makedirs(outbound_dir, exist_ok=True)
    yield inbound_dir, outbound_dir
    shutil.rmtree(base_dir, ignore_errors=True)

@pytest_asyncio.fixture
async def test_db_collection() -> AsyncIOMotorCollection:
    """Provides a clean database collection for each test."""
    client = AsyncIOMotorClient(TEST_MONGO_URI)
    db = client[TEST_MONGO_DB]
    collection = db[TEST_MONGO_COLLECTION]

    await collection.delete_many({})

    yield collection

    await client.drop_database(TEST_MONGO_DB)
    client.close()

@pytest.mark.asyncio
async def test_e2e_complete_flow(test_dirs, test_db_collection: AsyncIOMotorCollection):
    """
    Test the complete end-to-end flow of the integration service:
    1. Inbound: JSON file -> MongoDB
    2. Outbound: MongoDB -> JSON file
    """
    inbound_dir, outbound_dir = test_dirs
    collection = test_db_collection

    # --- 1. Arrange (Preparation) ---

    # a) Setup for INBOUND flow (Client -> TracOS)
    inbound_workorder_data = {
        "orderNo": 101,
        "summary": "Inbound Test: Check pump alignment",
        "creationDate": datetime.now(timezone.utc).isoformat(),
        "lastUpdateDate": datetime.now(timezone.utc).isoformat(),
        "isDone": True,
        "isCanceled": False,
        "isDeleted": False,
        "isOnHold": False,
        "isPending": False
    }
    inbound_file_path = os.path.join(inbound_dir, "inbound_101.json")
    with open(inbound_file_path, "w") as f:
        json.dump(inbound_workorder_data, f)

    # b) Setup for OUTBOUND flow (TracOS -> Client)
    outbound_workorder_data = {
        "_id": ObjectId(),
        "number": 202,
        "title": "Outbound Test: Replace filter",
        "description": "Filter is clogged, needs replacement.",
        "status": "pending",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "deleted": False,
        "isSynced": False
    }
    await collection.insert_one(outbound_workorder_data)

    # --- 2. Act (Execution) ---

    # Instantiate repositories with TEST configuration
    tracos_repo = TracOSRepository(
        mongo_uri=TEST_MONGO_URI,
        db_name=TEST_MONGO_DB,
        collection_name=TEST_MONGO_COLLECTION
    )
    client_repo = ClientRepository(inbound_dir=inbound_dir, outbound_dir=outbound_dir)

    # Inject repositories into the service
    service = IntegrationService(tracos_repo=tracos_repo, client_repo=client_repo)

    # Execute inbound cycle
    await service.tracos_repo.connect()
    await service.process_inbound()

    # --- 3. Assert (Verification) ---

    # a) Verify INBOUND flow
    inbound_result = await collection.find_one({"number": 101})
    assert inbound_result is not None
    assert inbound_result["title"] == "Inbound Test: Check pump alignment"
    assert inbound_result["status"] == "completed"
    assert inbound_result["isSynced"] is False

    await service.process_outbound()

    # b) Verify OUTBOUND flow
    outbound_file_path = os.path.join(outbound_dir, "202.json")
    assert os.path.exists(outbound_file_path)

    with open(outbound_file_path, "r") as f:
        outbound_result_json = json.load(f)

    assert outbound_result_json["orderNo"] == 202
    assert outbound_result_json["summary"] == "Outbound Test: Replace filter"
    assert outbound_result_json["isPending"] is True
    assert outbound_result_json["isSynced"] is True

    # c) Verify if the outbound item was marked as synchronized in the DB
    outbound_db_check = await collection.find_one({"number": 202})
    assert outbound_db_check is not None
    assert outbound_db_check["isSynced"] is True
    assert "syncedAt" in outbound_db_check
