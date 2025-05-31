import pytest
import os
import json
import shutil
from datetime import datetime, timezone
from bson import ObjectId
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import IntegrationService
from src.tracos.repository import TracOSRepository
from src.client.repository import ClientRepository

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
def mocked_tracos_repo():
    """
    Provides a TracOSRepository instance with a mocked MongoDB client,
    ensuring no real network connection is attempted.
    """
    with patch('src.tracos.repository.AsyncIOMotorClient') as MockMotorClient:
        mock_client_instance = MagicMock()
        MockMotorClient.return_value = mock_client_instance

        mock_admin_db = mock_client_instance.admin
        mock_admin_db.command = AsyncMock(return_value={"ok": 1})  # Simulate a successful ping

        repo = TracOSRepository(mongo_uri="mongodb://mockhost:12345", db_name="mockdb", collection_name="mockcollection")

        mock_db = mock_client_instance.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value

        repo.collection = mock_collection # Assign the mocked collection to the repo instance

        mock_collection.find_one = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_collection.find = MagicMock()

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock()
        mock_collection.find.return_value = mock_cursor

        yield repo

@pytest.mark.asyncio
async def test_e2e_complete_flow_mocked_db(test_dirs, mocked_tracos_repo: TracOSRepository):
    """
    Test the complete end-to-end flow of the integration service
    with a mocked MongoDB backend.
    """
    inbound_dir, outbound_dir = test_dirs
    tracos_repo_instance = mocked_tracos_repo

    # --- 1. Arrange (Preparation) ---
    # a) INBOUND flow setup
    inbound_workorder_data_client = {
        "orderNo": 101, "summary": "Inbound Test: Check pump alignment",
        "creationDate": datetime.now(timezone.utc).isoformat(), "lastUpdateDate": datetime.now(timezone.utc).isoformat(),
        "isDone": True, "isCanceled": False, "isDeleted": False, "isOnHold": False, "isPending": False
    }
    inbound_file_path = os.path.join(inbound_dir, "inbound_101.json")
    with open(inbound_file_path, "w") as f:
        json.dump(inbound_workorder_data_client, f)

    tracos_repo_instance.collection.find_one.return_value = None
    tracos_repo_instance.collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    # b) OUTBOUND flow setup
    outbound_id = ObjectId()
    tracos_outbound_data = {
        "_id": outbound_id, "number": 202, "title": "Outbound Test: Replace filter",
        "description": "Filter is clogged, needs replacement.", "status": "pending",
        "createdAt": datetime.now(timezone.utc), "updatedAt": datetime.now(timezone.utc),
        "deleted": False, "isSynced": False
    }
    tracos_repo_instance.collection.find.return_value.to_list.return_value = [tracos_outbound_data]
    tracos_repo_instance.collection.update_one.return_value = MagicMock(modified_count=1)

    # --- 2. Act (Execution) ---
    client_repo = ClientRepository(inbound_dir=inbound_dir, outbound_dir=outbound_dir)
    service = IntegrationService(tracos_repo=tracos_repo_instance, client_repo=client_repo)

    # This call will now use the mocked client and succeed
    await service.tracos_repo.connect()
    await service.process_inbound()

    # --- 3. Assert (Verification) ---
    # a) INBOUND flow verification
    tracos_repo_instance.collection.insert_one.assert_awaited_once()
    args_call = tracos_repo_instance.collection.insert_one.call_args[0][0]
    assert args_call["number"] == 101
    assert args_call["status"] == "completed"

    # b) OUTBOUND flow execution and verification
    await service.process_outbound()
    outbound_file_path = os.path.join(outbound_dir, "202.json")
    assert os.path.exists(outbound_file_path)

    with open(outbound_file_path, "r") as f:
        outbound_result_json = json.load(f)
    assert outbound_result_json["orderNo"] == 202
    assert outbound_result_json["isPending"] is True

    # c) Verify mark_as_synced was called
    found_mark_as_synced_call = False
    for call in tracos_repo_instance.collection.update_one.call_args_list:
        query_arg = call.args[0]
        update_arg = call.args[1]["$set"]
        if query_arg.get("_id") == outbound_id and update_arg.get("isSynced") is True:
            found_mark_as_synced_call = True
            break
    assert found_mark_as_synced_call, "mark_as_synced was not called as expected"
