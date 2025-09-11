from crewai_tools import RagTool
from typing import Type, Any
from pydantic.v1 import BaseModel, Field

from .github_helper import get_pr_diff

class PRDiffInput(BaseModel):
    """Input model for the PR Diff Tool."""
    repo_url: str = Field(..., description="The full URL of the repository.")
    pr_number: int = Field(..., description="The number of the pull request.")
    github_token: str = Field(None, description="Optional GitHub token for private repos.")

class GetPRDiffTool(RagTool):
    name: str = "GitHub PR Diff Tool"
    description: str = "Fetches the diff of a specific GitHub Pull Request to analyze code changes."
    args_schema: Type[BaseModel] = PRDiffInput
    
    def _run(self, repo_url: str, pr_number: int, github_token: str = None) -> str:
        """Use the tool."""
        try:
            # Note: The underlying 'requests' library is synchronous.
            # For a truly async implementation, an async HTTP client like httpx would be needed.
            # However, for crewai's tool structure, providing this method is best practice.
            return get_pr_diff(
                repo_url=repo_url, pr_number=pr_number, token=github_token
            )
        except Exception as e:
            return f"Error fetching PR diff: {e}"

    async def _arun(self, repo_url: str, pr_number: int, github_token: str = None) -> str:
        """Use the tool asynchronously."""
        # Since get_pr_diff is synchronous, we just wrap the synchronous call.
        return self._run(repo_url, pr_number, github_token)

    def _is_pydantic_class(self) -> bool:
        """Check if the args_schema is a Pydantic class."""
        return issubclass(self.args_schema, BaseModel)
