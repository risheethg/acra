import pytest
from fastapi import status
from unittest.mock import patch
from app.routes.analysis import results_cache # Import the cache to clear it

@pytest.fixture(autouse=True)
def clear_cache():
    """Clears the in-memory cache before each API test."""
    results_cache.clear()
    yield

def test_analyze_pr_endpoint(client, mock_async_result):
    """Test the POST /analyze-pr endpoint."""
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    response = client.post(
        "/api/v1/analyze-pr",
        json={"repo_url": repo_url, "pr_number": pr_number, "github_token": github_token}
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "PENDING"
    mock_async_result.delay.assert_called_once_with(repo_url, pr_number, github_token)

def test_get_status_pending(client, mock_async_result):
    """Test GET /status/{task_id} for a pending task."""
    mock_async_result.state = "PENDING"
    mock_async_result.ready.return_value = False

    response = client.get(f"/api/v1/status/{mock_async_result.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "PENDING"
    assert response.json()["detail"] is None

def test_get_status_processing(client, mock_async_result):
    """Test GET /status/{task_id} for a processing task."""
    mock_async_result.state = "PROCESSING"
    mock_async_result.info = {'status': 'Fetching PR diff...'}
    mock_async_result.ready.return_value = False

    response = client.get(f"/api/v1/status/{mock_async_result.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "PROCESSING"
    assert response.json()["detail"] == "Fetching PR diff..."

def test_get_status_failure(client, mock_async_result):
    """Test GET /status/{task_id} for a failed task."""
    mock_async_result.state = "FAILURE"
    mock_async_result.failed.return_value = True
    mock_async_result.result = ValueError("Test error message") # Simulate exception

    response = client.get(f"/api/v1/status/{mock_async_result.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "FAILURE"
    assert "Task failed with an error: Test error message" in response.json()["detail"]

def test_get_results_not_ready(client, mock_async_result):
    """Test GET /results/{task_id} when task is not ready."""
    mock_async_result.state = "PENDING"
    mock_async_result.ready.return_value = False

    response = client.get(f"/api/v1/results/{mock_async_result.id}")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "Task is not complete" in response.json()["detail"]

def test_get_results_failed(client, mock_async_result):
    """Test GET /results/{task_id} when task has failed."""
    mock_async_result.state = "FAILURE"
    mock_async_result.ready.return_value = True
    mock_async_result.failed.return_value = True

    response = client.get(f"/api/v1/results/{mock_async_result.id}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Task failed. Use the status endpoint for more details." in response.json()["detail"]

def test_get_results_completed(client, mock_async_result, mock_crew_analysis):
    """Test GET /results/{task_id} when task is completed successfully."""
    mock_async_result.state = "SUCCESS"
    mock_async_result.ready.return_value = True
    mock_async_result.failed.return_value = False
    mock_async_result.get.return_value = mock_crew_analysis # Return the expected dict

    response = client.get(f"/api/v1/results/{mock_async_result.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["results"] == mock_crew_analysis
    assert mock_async_result.id in results_cache # Check if cached

def test_get_results_from_cache(client, mock_async_result, mock_crew_analysis):
    """Test GET /results/{task_id} retrieves from cache on second call."""
    # First call to populate cache
    mock_async_result.state = "SUCCESS"
    mock_async_result.ready.return_value = True
    mock_async_result.failed.return_value = False
    mock_async_result.get.return_value = mock_crew_analysis

    client.get(f"/api/v1/results/{mock_async_result.id}")

    # Reset mock to ensure .get() is not called again
    mock_async_result.get.reset_mock()

    # Second call should hit cache
    response = client.get(f"/api/v1/results/{mock_async_result.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["task_id"] == mock_async_result.id
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["results"] == mock_crew_analysis
    mock_async_result.get.assert_not_called() # Verify it came from cache
