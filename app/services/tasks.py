import logging
import json
from app.core.celery_app import celery_app
from app.models.analysis import AnalysisResultData
# Change 1: Import the new LangChain function
from app.services.analyzer import analyze_code_with_langchain
from app.services.github_helper import get_pr_diff, GitHubConnectionError

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def run_code_analysis_task(self, repo_url: str, pr_number: int, github_token: str | None = None):
    # Change 2: Removed the temporary token logging for cleaner code
    try:
        logger.info(f"Starting analysis for {repo_url} PR #{pr_number}")
        self.update_state(state='PROCESSING', meta={'status': 'Fetching PR diff...'})

        pr_diff = get_pr_diff(repo_url, pr_number, github_token)
        
        self.update_state(state='PROCESSING', meta={'status': 'PR diff fetched. Starting AI analysis...'})
        logger.info("PR diff fetched successfully. Starting AI analysis...")

        # Change 3: Call the new LangChain function
        analysis_result_str = analyze_code_with_langchain(pr_diff)
        
        self.update_state(state='PROCESSING', meta={'status': 'AI analysis complete. Parsing results...'})
        logger.info("AI analysis complete. Parsing results.")
        
        try:
            analysis_result_json = json.loads(analysis_result_str)
            # Optional: Validate the structure before returning
            AnalysisResultData(**analysis_result_json)
            return analysis_result_json
        except json.JSONDecodeError:
            error_message = "The AI agent returned a malformed JSON response."
            logger.error(f"{error_message} Raw output: {analysis_result_str}", exc_info=True)
            self.update_state(state='FAILURE', meta={'status': 'Task failed', 'error': error_message})
            raise ValueError(error_message)
    
    # Catch the specific error from our helper
    except GitHubConnectionError as e:
        error_message = str(e)
        logger.error(f"Task failed due to connection issue: {error_message}", exc_info=True)
        self.update_state(state='FAILURE', meta={'status': 'Task failed', 'error': error_message})
        raise
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.error(f"An unexpected error occurred in task for {repo_url} PR #{pr_number}: {error_message}", exc_info=True)
        self.update_state(state='FAILURE', meta={'status': 'Task failed', 'error': str(e)})
        raise