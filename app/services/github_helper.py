import base64
from github import Github, GithubException
import requests
from urllib.parse import urlparse

def get_pr_diff(repo_url: str, pr_number: int, token: str = None) -> str:
    """
    Fetches the diff of a specific pull request from a GitHub repository.
    """
    try:
        g = Github(token)
        parsed_url = urlparse(repo_url)
        repo_name = parsed_url.path.strip('/')
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Fetch the diff content directly from the PR's diff_url
        # This provides the unified diff for the entire PR
        headers = {'Authorization': f'token {token}'} if token else {}
        headers['Accept'] = 'application/vnd.github.v3.diff'
        
        response = requests.get(pr.diff_url, headers=headers)
        response.raise_for_status() # Will raise an HTTPError for bad responses
        
        return response.text
    except GithubException as e:
        raise ConnectionError(f"Failed to connect to GitHub or find PR: {e.data}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while fetching PR diff: {e}")
