import time
import logging
import json
from celery import shared_task

from .agent_tools import run_code_analysis_crew
from ..models.analysis import AnalysisResultData

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def run_code_analysis_task(self, repo_url: str, pr_number: int, github_token: str = None):
    """A Celery task to run the AI code review agent."""
    try:
        logger.info(f"Starting analysis for {repo_url} PR #{pr_number}")
        self.update_state(state='PROCESSING', meta={'status': 'Initializing AI agent...'})

        # Run the CrewAI agent to get the analysis
        analysis_result_str = run_code_analysis_crew(repo_url, pr_number, github_token)
        
        self.update_state(state='PROCESSING', meta={'status': 'Parsing AI response...'})
        logger.info(f"Agent finished. Raw result: {analysis_result_str}")

        # The output from CrewAI might be a string, so we need to parse it.
        # It's crucial that the LLM is prompted to return clean JSON.
        try:
            # Clean potential markdown code blocks
            if analysis_result_str.strip().startswith("```json"):
                analysis_result_str = analysis_result_str.strip()[7:-4]

            analysis_result_json = json.loads(analysis_result_str)
            
            # Validate with Pydantic
            validated_result = AnalysisResultData(**analysis_result_json)
            
        except (json.JSONDecodeError, TypeError, Exception) as e:
            logger.error(f"Failed to parse or validate AI response for task {self.request.id}: {e}")
            raise ValueError("The AI agent returned a malformed JSON response.")

        logger.info(f"Analysis complete for task {self.request.id}")
        return validated_result.dict()

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}", exc_info=True)
        # The state will be automatically set to 'FAILURE' by Celery
        # and the exception will be stored as the result.
        raise  # Re-raise the exception to let Celery know the task failed
