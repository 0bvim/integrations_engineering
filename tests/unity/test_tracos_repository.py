import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from src.tracos.repository import TracOSRepository

# Mock the AsyncIOMotorClient class to prevent real connections
@pytest_asyncio.fixture
async def mock_repo():
    """Fixture that provides a repository instance with a mocked DB client."""
    with patch('motor.motor_asyncio.AsyncIOMotorClient') as MockMotorClient:
        mock_client_instance = MockMotorClient.return_value
        mock_db = mock_client_instance.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value

        repo = TracOSRepository()
        repo.client = mock_client_instance
        repo.db = mock_db
        repo.collection = mock_collection

        # Define methods as AsyncMock by default
        mock_collection.find_one = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_collection.find = MagicMock()

        yield repo, mock_collection

@pytest.mark.asyncio
class TestTracOSRepository:

    async def test_get_unsynchronized_workorders(self, mock_repo):
        """Tests if the method for fetching unsynchronized workorders works."""
        repo, mock_collection = mock_repo

        # Arrange: Configure the mock's return value to be awaitable
        mock_cursor = mock_collection.find.return_value
        mock_cursor.to_list = AsyncMock(return_value=[{"number": 1, "isSynced": False}])

        # Act
        result = await repo.get_unsynchronized_workorders()

        # Assert
        mock_collection.find.assert_called_once_with({"isSynced": False})
        assert len(result) == 1
        assert result[0]["number"] == 1

    async def test_create_new_workorder_when_not_exists(self, mock_repo):
        """Tests the creation of a new workorder."""
        repo, mock_collection = mock_repo
        workorder = {"number": 123, "title": "New WO"}

        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        # Act
        result = await repo.create_or_update_workorder(workorder)

        # Assert
        assert result is True
        mock_collection.find_one.assert_awaited_once_with({"number": 123})
        mock_collection.insert_one.assert_awaited_once()
        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert "createdAt" in inserted_doc
        assert inserted_doc["isSynced"] is False

    async def test_update_existing_workorder(self, mock_repo):
        """Tests updating an existing workorder."""
        repo, mock_collection = mock_repo
        existing_wo = {"number": 123, "title": "Old Title", "status": "pending", "description": "", "deleted": False}
        new_wo_data = {"number": 123, "title": "New Title", "status": "completed", "description": "", "deleted": False}

        mock_collection.find_one.return_value = existing_wo
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        result = await repo.create_or_update_workorder(new_wo_data)

        # Assert
        assert result is True
        mock_collection.find_one.assert_awaited_once_with({"number": 123})
        mock_collection.update_one.assert_awaited_once()
        update_doc = mock_collection.update_one.call_args[0][1]["$set"]
        assert update_doc["isSynced"] is False
        assert update_doc["title"] == "New Title"

    async def test_skip_update_if_no_changes(self, mock_repo):
        """Tests if the update is skipped when there are no changes."""
        repo, mock_collection = mock_repo
        existing_wo = {"number": 123, "title": "Same Title", "status": "pending", "description": "", "deleted": False}
        new_wo_data = {"number": 123, "title": "Same Title", "status": "pending", "description": "", "deleted": False}

        # Arrange: find_one returns the existing document when awaited
        mock_collection.find_one.return_value = existing_wo

        # Act
        result = await repo.create_or_update_workorder(new_wo_data)

        # Assert
        assert result is True
        mock_collection.find_one.assert_awaited_once_with({"number": 123})
        mock_collection.update_one.assert_not_awaited()

    async def test_mark_as_synced(self, mock_repo):
        """Tests if marking as 'synced' works."""
        repo, mock_collection = mock_repo
        workorder_id = "60c72b2f9b1e8b3b4c8b4567"

        # Arrange: update_one returns an object with modified_count when awaited
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        result = await repo.mark_as_synced(workorder_id)

        # Assert
        assert result is True
        mock_collection.update_one.assert_awaited_once()
        query_arg = mock_collection.update_one.call_args[0][0]
        update_arg = mock_collection.update_one.call_args[0][1]["$set"]

        assert query_arg["_id"] == ObjectId(workorder_id)
        assert update_arg["isSynced"] is True
        assert "syncedAt" in update_arg
