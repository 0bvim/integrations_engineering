import pytest
from src.client.repository import ClientRepository
import json
import os

@pytest.fixture
def data_dirs(tmp_path):
    # Use pytest's tmp_path for isolated, auto-cleaned temp directories
    inbound_dir = tmp_path / "inbound"
    outbound_dir = tmp_path / "outbound"
    inbound_dir.mkdir()
    outbound_dir.mkdir()
    return str(inbound_dir), str(outbound_dir)

@pytest.fixture
def create_n_orders():
    def _create(n, inbound_dir):
        for i in range(1, n + 1):
            workorder = {
                "orderNo": i,
                "isCanceled": False,
                "isDeleted": False,
                "isDone": False,
                "isOnHold": False,
                "isPending": True,
                "summary": f"Example workorder #{i}",
                "creationDate": "2025-05-01T22:36:24.105812+00:00",
                "lastUpdateDate": "2025-05-01T23:36:24.105812+00:00",
                "deletedDate": "2025-05-01T23:36:24.105812+00:00"
            }
            with open(os.path.join(inbound_dir, f"workorder_{i}.json"), "w") as f:
                json.dump(workorder, f)
    return _create

@pytest.mark.asyncio
async def test_empty(data_dirs):
    inbound_dir, outbound_dir = data_dirs
    client = ClientRepository(inbound_dir, outbound_dir)
    result = await client.get_inbound_workorders()
    assert result == []

@pytest.mark.asyncio
@pytest.mark.parametrize("n_orders", [1, 5, 10, 50, 100])
async def test_n_orders(data_dirs, create_n_orders, n_orders):
    inbound_dir, outbound_dir = data_dirs
    create_n_orders(n_orders, inbound_dir)
    client = ClientRepository(inbound_dir, outbound_dir)
    result = await client.get_inbound_workorders()
    assert len(result) == n_orders

@pytest.mark.asyncio
@pytest.mark.parametrize("n_orders", [1])
async def test_order_content(data_dirs, create_n_orders, n_orders):
    inbound_dir, outbound_dir = data_dirs
    create_n_orders(n_orders, inbound_dir)
    client = ClientRepository(inbound_dir, outbound_dir)
    result = await client.get_inbound_workorders()
    assert len(result) == 1
    assert result[0]["orderNo"] == 1
    assert result[0]["isCanceled"] is False
    assert result[0]["isDeleted"] is False
    assert result[0]["isDone"] is False
    assert result[0]["isOnHold"] is False
    assert result[0]["isPending"] is True
    assert "summary" in result[0]
    assert "creationDate" in result[0]
    assert "lastUpdateDate" in result[0]
    assert "deletedDate" in result[0]
