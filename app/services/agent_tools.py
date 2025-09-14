from crewai_tools import tool
from pydantic.v1 import BaseModel, Field

# Corrected absolute import
from app.services.github_helper import get_pr_diff, GitHubConnectionError

class PRDiffInput(BaseModel):
    """Input model for the PR Diff Tool."""
    repo_url: str = Field(..., description="The full URL of the repository.")
    pr_number: int = Field(..., description="The number of the pull request.")
    github_token: str = Field(None, description="Optional GitHub token for private repos.")

@tool("GitHub PR Diff Tool", args_schema=PRDiffInput)
def get_pr_diff_tool(repo_url: str, pr_number: int, github_token: str = None) -> str:
    """
    Fetches the diff of a specific GitHub Pull Request to analyze code changes.
    Returns the full diff as a single string.
    If the PR is not found or another error occurs, this tool will raise an exception.
    """
    # By removing the try/except, any exception from get_pr_diff (like GitHubConnectionError)
    # will now propagate up, causing the crew/agent to fail, which is the correct behavior.
    return get_pr_diff(repo_url=repo_url, pr_number=pr_number, token=github_token)