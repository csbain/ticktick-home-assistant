#!/usr/bin/env python3
"""Test get_subtasks service handler."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from custom_components.ticktick.service_handlers import handle_get_subtasks
from custom_components.ticktick.ticktick_api_python.models.task import TaskStatus


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = Mock()
    return client


@pytest.fixture
def task_with_subtasks_response():
    """Mock API response for task with subtasks."""
    return {
        "id": "task123",
        "title": "Grocery Shopping",
        "projectId": "proj1",
        "items": [
            {
                "id": "sub1",
                "title": "Buy milk",
                "status": TaskStatus.COMPLETED_1.value,
                "sortOrder": 0
            },
            {
                "id": "sub2",
                "title": "Buy eggs",
                "status": TaskStatus.COMPLETED_1.value,
                "sortOrder": 1
            },
            {
                "id": "sub3",
                "title": "Buy bread",
                "status": TaskStatus.COMPLETED_1.value,
                "sortOrder": 2
            },
            {
                "id": "sub4",
                "title": "Buy butter",
                "status": TaskStatus.NORMAL.value,
                "sortOrder": 3
            },
            {
                "id": "sub5",
                "title": "Buy cheese",
                "status": TaskStatus.NORMAL.value,
                "sortOrder": 4
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_subtasks_success(mock_client, task_with_subtasks_response):
    """Test successful get_subtasks service call."""
    # Setup mock
    mock_client.get_task = AsyncMock(return_value=task_with_subtasks_response)

    # Create handler
    handler = await handle_get_subtasks(mock_client)

    # Create mock service call
    service_call = Mock()
    service_call.data = {
        "project_id": "proj1",
        "task_id": "task123"
    }

    # Call handler
    await handler(service_call)

    # Verify response
    response = service_call.response
    assert "data" in response
    assert response["data"]["task_id"] == "task123"
    assert response["data"]["task_title"] == "Grocery Shopping"
    assert response["data"]["subtask_total"] == 5
    assert response["data"]["subtask_completed"] == 3
    assert response["data"]["subtask_progress_percent"] == 60
    assert len(response["data"]["subtasks"]) == 5

    # Verify first subtask
    subtask1 = response["data"]["subtasks"][0]
    assert subtask1["id"] == "sub1"
    assert subtask1["title"] == "Buy milk"
    assert subtask1["status"] == "completed"
    assert subtask1["sort_order"] == 0

    # Verify API was called correctly
    mock_client.get_task.assert_called_once_with(
        projectId="proj1",
        taskId="task123",
        returnAsJson=True
    )


@pytest.mark.asyncio
async def test_get_subtasks_missing_parameters(mock_client):
    """Test get_subtasks with missing parameters."""
    handler = await handle_get_subtasks(mock_client)

    # Test missing project_id
    service_call = Mock()
    service_call.data = {"task_id": "task123"}
    await handler(service_call)
    assert "error" in service_call.response
    assert "required" in service_call.response["error"]

    # Test missing task_id
    service_call.data = {"project_id": "proj1"}
    await handler(service_call)
    assert "error" in service_call.response
    assert "required" in service_call.response["error"]

    # Test both missing
    service_call.data = {}
    await handler(service_call)
    assert "error" in service_call.response


@pytest.mark.asyncio
async def test_get_subtasks_task_not_found(mock_client):
    """Test get_subtasks when task doesn't exist."""
    mock_client.get_task = AsyncMock(return_value=None)

    handler = await handle_get_subtasks(mock_client)

    service_call = Mock()
    service_call.data = {
        "project_id": "proj1",
        "task_id": "nonexistent"
    }

    await handler(service_call)

    response = service_call.response
    assert "error" in response
    assert "not found" in response["error"]


@pytest.mark.asyncio
async def test_get_subtasks_no_subtasks(mock_client):
    """Test get_subtasks for task with no subtasks."""
    task_response = {
        "id": "task456",
        "title": "Simple Task",
        "projectId": "proj1",
        "items": []
    }

    mock_client.get_task = AsyncMock(return_value=task_response)

    handler = await handle_get_subtasks(mock_client)

    service_call = Mock()
    service_call.data = {
        "project_id": "proj1",
        "task_id": "task456"
    }

    await handler(service_call)

    response = service_call.response
    assert response["data"]["subtask_total"] == 0
    assert response["data"]["subtask_completed"] == 0
    assert response["data"]["subtask_progress_percent"] == 0
    assert len(response["data"]["subtasks"]) == 0
