import pytest
import json
from app.services.tasks import run_code_analysis_task
from app.services.github_helper import GitHubConnectionError
from app.models.analysis import AnalysisResultData

def test_run_code_analysis_task_success(celery_app, mocker, mock_github_diff):
    """
    Test successful execution of run_code_analysis_task.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the analyzer to return a valid JSON string
    mock_analysis_json = '{"files": [{"name": "main.py", "issues": [{"type": "style", "line": 1, "description": "desc", "suggestion": "sugg"}]}], "summary": {"total_files": 1, "total_issues": 1, "critical_issues": 0}}'
    mocker.patch("app.services.tasks.analyze_code_with_langchain", return_value=mock_analysis_json)

    result = run_code_analysis_task.delay(repo_url, pr_number, github_token).get()

    # Validate the returned result structure
    assert isinstance(result, dict)
    validated_result = AnalysisResultData(**result) # Pydantic validation
    assert validated_result.files[0].name == "main.py"
    assert validated_result.summary.total_issues == 1
    assert validated_result.files[0].issues[0].type == "style"

def test_run_code_analysis_task_malformed_json(celery_app, mocker, mock_github_diff):
    """
    Test run_code_analysis_task when the AI returns malformed JSON.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the analyzer to return invalid JSON
    mocker.patch("app.services.tasks.analyze_code_with_langchain", return_value="this is not json")

    task = run_code_analysis_task.delay(repo_url, pr_number, github_token)
    
    # Expect a ValueError because of JSON decoding failure
    with pytest.raises(ValueError, match="The AI returned a malformed JSON response."):
        task.get()

def test_run_code_analysis_task_analyzer_exception(celery_app, mocker, mock_github_diff):
    """
    Test run_code_analysis_task when the analyzer raises an internal exception.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the analyzer to raise an exception
    mocker.patch("app.services.tasks.analyze_code_with_langchain", side_effect=Exception("Analyzer internal error"))

    task = run_code_analysis_task.delay(repo_url, pr_number, github_token)
    
    # Expect the original exception to be propagated by Celery
    with pytest.raises(Exception, match="Analyzer internal error"):
        task.get()

def test_run_code_analysis_task_github_connection_error(celery_app, mocker):
    """
    Test run_code_analysis_task when GitHub connection fails.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock get_pr_diff to raise our custom connection error
    mocker.patch(
        "app.services.tasks.get_pr_diff",
        side_effect=GitHubConnectionError("GitHub API down")
    )

    task = run_code_analysis_task.delay(repo_url, pr_number, github_token)

    with pytest.raises(GitHubConnectionError, match="GitHub API down"):
        task.get()
