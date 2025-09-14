import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Import the main FastAPI app
from main import app as fastapi_app

# Import the Celery app
from app.core.celery_app import celery_app as _celery_app

@pytest.fixture(scope="module")
def client():
    """Provides a test client for FastAPI application."""
    with TestClient(fastapi_app) as c:
        yield c

@pytest.fixture(scope="function")
def celery_app(mocker):
    """
    Configures Celery to run tasks synchronously (eagerly) for testing.
    This avoids needing a running Celery worker and Redis during tests.
    """
    _celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url='memory://', # Use an in-memory broker for eager execution
        result_backend='cache+memory://' # Use an in-memory result backend
    )
    yield _celery_app
    # Reset Celery config after tests if necessary, though task_always_eager is usually enough
    _celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
        broker_url='redis://redis:6379/0', # Restore original broker
        result_backend='redis://redis:6379/0' # Restore original backend
    )

@pytest.fixture
def mock_async_result(mocker):
    """
    Fixture to mock Celery's AsyncResult for API endpoint testing.
    """
    mock_result = MagicMock()
    mock_result.id = "mock_task_id_123"
    mock_result.state = "PENDING"
    mock_result.info = {}
    mock_result.ready.return_value = False
    mock_result.failed.return_value = False
    mock_result.get.return_value = None # Default for pending/processing

    # Patch AsyncResult to return our mock
    mocker.patch("app.routes.analysis.AsyncResult", return_value=mock_result)
    
    # Patch the .delay() method of the task to return our mock AsyncResult
    mocker.patch("app.services.tasks.run_code_analysis_task.delay", return_value=mock_result)

    return mock_result

@pytest.fixture
def mock_crew_analysis(mocker):
    """
    Fixture to mock the run_code_analysis_crew function.
    """
    mock_output = {
        "files": [
            {
                "name": "main.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 15,
                        "description": "Line too long",
                        "suggestion": "Break line into multiple lines"
                    }
                ]
            }
        ],
        "summary": {
            "total_files": 1,
            "total_issues": 1,
            "critical_issues": 0
        }
    }
    mocker.patch("app.services.crew.run_code_analysis_crew", return_value=mock_output)
    return mock_output

@pytest.fixture
def mock_github_diff(mocker):
    """
    Fixture to mock the get_pr_diff function.
    """
    mocker.patch("app.services.github_helper.get_pr_diff", return_value="diff content here")
    # Also patch the tool's internal call to it
    mocker.patch("app.services.agent_tools.get_pr_diff", return_value="diff content here")
    return "diff content here"
