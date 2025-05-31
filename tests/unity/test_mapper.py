import pytest
from datetime import datetime, timezone
from src.translation.mapper import WorkorderMapper

# Fixtures with sample data
@pytest.fixture
def sample_client_workorder():
    return {
        "orderNo": 101,
        "summary": "Test Summary",
        "description": "Test Description",
        "creationDate": "2025-05-30T10:00:00.000Z",
        "lastUpdateDate": "2025-05-30T11:00:00.000Z",
        "isDone": False,
        "isCanceled": False,
        "isDeleted": False,
        "isOnHold": False,
        "isPending": True,
    }

@pytest.fixture
def sample_tracos_workorder():
    return {
        "number": 202,
        "title": "TracOS Title",
        "description": "TracOS Description",
        "status": "in_progress",
        "createdAt": datetime(2025, 5, 30, 10, 0, 0, tzinfo=timezone.utc),
        "updatedAt": datetime(2025, 5, 30, 11, 0, 0, tzinfo=timezone.utc),
        "deleted": False,
        "isSynced": False
    }

class TestWorkorderMapper:

    @pytest.mark.parametrize("client_status, tracos_status", [
        ({"isDone": True}, "completed"),
        ({"isOnHold": True}, "on_hold"),
        ({"isCanceled": True}, "cancelled"),
        ({"isDeleted": True}, "cancelled"),
        ({"isPending": True}, "pending"),
        ({"isPending": False}, "in_progress"),
    ])
    def test_client_to_tracos_status_mapping(self, sample_client_workorder, client_status, tracos_status):
        """Tests the mapping of all client status to TracOS."""
        client_data = {**sample_client_workorder, **client_status}
        tracos_result = WorkorderMapper.client_to_tracos(client_data)
        assert tracos_result["status"] == tracos_status

    def test_client_to_tracos_full_conversion(self, sample_client_workorder):
        """Tests the complete conversion of a client object to TracOS."""
        tracos_result = WorkorderMapper.client_to_tracos(sample_client_workorder)

        assert tracos_result["number"] == 101
        assert tracos_result["title"] == "Test Summary"
        assert tracos_result["status"] == "pending"
        assert isinstance(tracos_result["createdAt"], datetime)
        assert tracos_result["createdAt"].year == 2025

    @pytest.mark.parametrize("tracos_status, client_status_flags", [
        ("completed", {"isDone": True, "isPending": False}),
        ("on_hold", {"isOnHold": True, "isPending": False}),
        ("cancelled", {"isCanceled": True, "isPending": False}),
        ("pending", {"isPending": True, "isDone": False}),
        ("in_progress", {"isPending": False, "isDone": False, "isOnHold": False, "isCanceled": False}),
    ])
    def test_tracos_to_client_status_mapping(self, sample_tracos_workorder, tracos_status, client_status_flags):
        """Tests the mapping of all TracOS status to client."""
        tracos_data = {**sample_tracos_workorder, "status": tracos_status}
        client_result = WorkorderMapper.tracos_to_client(tracos_data)

        for flag, expected_value in client_status_flags.items():
            assert client_result[flag] is expected_value

    def test_tracos_to_client_full_conversion(self, sample_tracos_workorder):
        """Tests the complete conversion of a TracOS object to client."""
        client_result = WorkorderMapper.tracos_to_client(sample_tracos_workorder)

        assert client_result["orderNo"] == 202
        assert client_result["summary"] == "TracOS Title"
        assert client_result["isSynced"] is True
        assert client_result["creationDate"] == "2025-05-30T10:00:00+00:00"

    def test_handles_missing_dates(self, sample_client_workorder):
        """Tests if the mapper handles missing dates without failing."""
        del sample_client_workorder["creationDate"]
        tracos_result = WorkorderMapper.client_to_tracos(sample_client_workorder)
        assert isinstance(tracos_result["createdAt"], datetime)
