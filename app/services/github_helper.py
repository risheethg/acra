import logging
from urllib.parse import urlparse
import requests
from github import Github, UnknownObjectException, GithubException

logger = logging.getLogger(__name__)

class GitHubConnectionError(Exception):
    """Custom exception for GitHub-related connection or access errors."""
    pass

def get_pr_diff(repo_url: str, pr_number: int, token: str | None = None) -> str:
    """
    Fetches the diff of a specific GitHub Pull Request.
    """
    repo_name = None # Initialize repo_name
    try:
        if not token:
            logger.warning("No GitHub token provided. Rate limits will be low.")
        g = Github(token)
        
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL format.")
        
        owner, repo_slug = path_parts[:2]
        repo_name = f"{owner}/{repo_slug}"
        logger.info(f"Accessing repository: {repo_name}")
        
        repo = g.get_repo(repo_name)
        
        logger.info(f"Fetching PR #{pr_number}")
        pr = repo.get_pull(pr_number)
        
        # *** ADDED THIS LINE ***
        # Access an attribute to force an API call and confirm the PR exists.
        # If it doesn't, this will raise UnknownObjectException.
        _ = pr.title 
        
        # Check if the PR is a draft, as they don't have a diff_url that works.
        if pr.draft:
            error_msg = f"Pull Request #{pr_number} in repository '{repo_name}' is a draft. Draft PRs cannot be analyzed."
            raise GitHubConnectionError(error_msg)

        headers = {'Accept': 'application/vnd.github.v3.diff'}
        if token:
            headers['Authorization'] = f'token {token}'
        
        # Now we are more confident that pr.diff_url will point to a valid resource
        response = requests.get(pr.diff_url, headers=headers)
        response.raise_for_status() # Will raise an HTTPError for bad responses (4xx or 5xx)
        
        diff = response.text
        logger.info(f"Successfully fetched diff for PR #{pr_number}")
        return diff
        
    except UnknownObjectException:
        if repo_name:
            error_msg = f"Repository '{repo_name}' or PR '#{pr_number}' not found. Please check the URL, PR number, and your token permissions for private repos."
        else:
            error_msg = f"Could not find the requested repository or PR '#{pr_number}'. Please check the URL."
        logger.error(error_msg)
        raise GitHubConnectionError(error_msg)
        
    except GithubException as e:
        error_msg = f"An error occurred with the GitHub API: {e.data.get('message', 'Unknown error')}"
        logger.error(error_msg)
        raise GitHubConnectionError(error_msg) from e
        
    except Exception as e:
        # Catch requests.exceptions.HTTPError here as well
        error_msg = f"An unexpected error occurred: {e}"
        logger.error(error_msg)
        raise GitHubConnectionError(error_msg) from e