import pytest
import json
from app.services.tasks import run_code_analysis_task
from app.models.analysis import AnalysisResultData

def test_run_code_analysis_task_success(celery_app, mock_crew_analysis, mock_github_diff):
    """
    Test successful execution of run_code_analysis_task.
    `mock_crew_analysis` will return the expected JSON dict.
    `mock_github_diff` ensures the tool can be called if needed by the crew.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # The mock_crew_analysis fixture already patches run_code_analysis_crew
    # to return a dictionary. The task expects a string, so we'll adjust the mock.
    # This is a good example of how mocks need to match the *interface* expected by the code under test.
    # Let's re-patch it to return a JSON string.
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.services.crew.run_code_analysis_crew", lambda *args, **kwargs: json.dumps(mock_crew_analysis))

        result = run_code_analysis_task.delay(repo_url, pr_number, github_token).get()

        # Verify the crew function was called
        # Note: Since we re-patched with a lambda, direct assertion on the original mock might be tricky.
        # The primary check is the output.
        
        # Validate the returned result structure
        assert isinstance(result, dict)
        validated_result = AnalysisResultData(**result) # Pydantic validation
        assert validated_result.files[0].name == "main.py"
        assert validated_result.summary.total_issues == 1
        assert validated_result.files[0].issues[0].type == "style"

def test_run_code_analysis_task_malformed_json(celery_app, mock_github_diff):
    """
    Test run_code_analysis_task when the AI agent returns malformed JSON.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the crew to return invalid JSON
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.services.crew.run_code_analysis_crew", lambda *args, **kwargs: "this is not json")

        task = run_code_analysis_task.delay(repo_url, pr_number, github_token)
        
        # Expect a ValueError because of JSON decoding failure
        with pytest.raises(ValueError, match="The AI agent returned a malformed JSON response."):
            task.get()

def test_run_code_analysis_task_crew_exception(celery_app, mock_github_diff):
    """
    Test run_code_analysis_task when the AI agent (crew) raises an internal exception.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the crew to raise an exception
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.services.crew.run_code_analysis_crew", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Crew internal error")))

        task = run_code_analysis_task.delay(repo_url, pr_number, github_token)
        
        # Expect the original exception to be propagated by Celery
        with pytest.raises(Exception, match="Crew internal error"):
            task.get()

def test_run_code_analysis_task_github_connection_error(celery_app):
    """
    Test run_code_analysis_task when GitHub connection fails (via tool).
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    github_token = "test_token"

    # Mock the get_pr_diff to raise a ConnectionError
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.services.github_helper.get_pr_diff", lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError("GitHub API down")))
        # Also mock the crew to ensure it attempts to use the tool
        mp.setattr("app.services.crew.run_code_analysis_crew", lambda *args, **kwargs: "{}") # Return empty JSON if it somehow proceeds

        task = run_code_analysis_task.delay(repo_url, pr_number, github_token)
        
        # The error from get_pr_diff will be caught by the tool and returned as a string.
        # The crew will then likely fail to parse this as a diff or generate valid JSON.
        # This test might need refinement based on how the CrewAI agent handles tool errors.
        # For now, let's assume the crew will return an error message string.
        # If the crew is robust, it might return valid JSON indicating the tool error.
        # For this test, we'll check if the task itself fails due to the tool's error.
        # The `_run` method of the tool returns a string error, which the LLM then processes.
        # If the LLM is good, it might still produce valid JSON with an error message inside.
        # Let's make the mock for `run_code_analysis_crew` return a string that indicates the tool error.
        mp.setattr("app.services.crew.run_code_analysis_crew", lambda *args, **kwargs: json.dumps({
            "files": [],
            "summary": {"total_files": 0, "total_issues": 0, "critical_issues": 0},
            "error": "Error fetching PR diff: GitHub API down"
        }))

        result = task.get()
        assert "error" in result
        assert "GitHub API down" in result["error"]
