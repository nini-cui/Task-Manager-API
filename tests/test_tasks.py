import pytest, pytest_asyncio, asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app, task_manager
from app.models import TaskRequest

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_submit_task(client):
    task_request = {"parameters": {"numbers": [1,2,3]}, "task_type": "COMPUTE_SUM"}
    response = await client.post("/tasks", json=task_request)
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_task_processing(monkeypatch):
    # Patch asyncio.sleep to skip delays
    async def fast_sleep(duration):
        return

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    task_request = TaskRequest(parameters={"numbers": [1,2,3]}, task_type="COMPUTE_SUM")
    task_id = await task_manager.submit_task(task_request)

    # Manually run the task processor
    await task_manager.process_task(task_id)

    task = task_manager.tasks_status[task_id]
    assert task["status"] == "completed"
    assert task["result"] == 6

@pytest.mark.asyncio
async def test_cancel_task():
    task_request = TaskRequest(parameters={"numbers": [1,2,3]}, task_type="COMPUTE_SUM")
    task_id = await task_manager.submit_task(task_request)

    cancelled = await task_manager.cancel_task(task_id)
    assert cancelled is True
    task = task_manager.tasks_status[task_id]
    assert task["status"] == "cancelled"

import pytest
import asyncio
from app.main import task_manager
from app.models import TaskRequest

@pytest.mark.asyncio
async def test_wait_for_task(monkeypatch):
    # Properly patch asyncio.sleep to skip delays
    async def fast_sleep(duration):
        return

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    task_request = TaskRequest(parameters={"numbers": [4,5]}, task_type="COMPUTE_SUM")
    task_id = await task_manager.submit_task(task_request)

    # Schedule task processing concurrently
    asyncio.create_task(task_manager.process_task(task_id))

    task = await task_manager.wait_for_task(task_id)
    assert task["status"] == "completed"
    assert task["result"] == 9

@pytest.mark.asyncio
async def test_concurrent_submissions(monkeypatch):
    async def fast_sleep(duration):
        return

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)
    
    tasks = [
        TaskRequest(parameters={"numbers": [i, i+1]}, task_type="COMPUTE_SUM")
        for i in range(10)
    ]

    task_ids = [await task_manager.submit_task(t) for t in tasks]

    # Run all tasks concurrently
    await asyncio.gather(*(task_manager.process_task(tid) for tid in task_ids))

    # Assert all tasks completed correctly
    for i, tid in enumerate(task_ids):
        t = task_manager.tasks_status[tid]
        assert t["status"] == "completed"
        assert t["result"] == i + (i+1)