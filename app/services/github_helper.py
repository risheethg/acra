import base64
from github import Github, GithubException
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
        
        # The diff is available as a raw string from the API
        # We need to make a request to the diff_url
        diff_content = pr.get_files()
        diff_text = ""
        for file in diff_content:
            diff_text += f"--- a/{file.filename}\n"
            diff_text += f"+++ b/{file.filename}\n"
            diff_text += file.patch + "\n"
        
        return diff_text
    except GithubException as e:
        raise ConnectionError(f"Failed to connect to GitHub or find PR: {e.data}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while fetching PR diff: {e}")
